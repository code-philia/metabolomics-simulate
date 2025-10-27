"""
liver_metabolism_sim.py

用法:
    python liver_metabolism_sim.py
"""

from collections import Counter
from dataclasses import dataclass
from typing import Dict, Callable, Union, Optional
import matplotlib.pyplot as plt
import threading
import queue
import re
import time


# plt.rcParams['font.sans-serif'] = ['SimHei']
# plt.rcParams['axes.unicode_minus'] = False

# 类型：产物字典可以是静态的 Dict[str,int] 或者是一个函数，函数根据 consumed_inputs 和 全局 pool 计算产物
OutputsType = Union[Dict[str, int], Callable[[Dict[str,int], Counter], Dict[str,int]]]

@dataclass
class Reaction:
    name: str
    inputs: Dict[str, int]  # 消耗的底物及计数（以单位反应为准）
    outputs: OutputsType    # 产生的产物，或一个函数计算
    # 可选：最大每步并行次数等


class MetabolicSimulator:
    def __init__(self, reactions, initial_pool: Optional[Dict[str,int]] = None, workers: int = 4):
        self.reactions = reactions
        self.pool = Counter(initial_pool or {})
        self.lock = threading.Lock()
        self.exec_count = Counter()  # 每个反应的执行总次数
        self.workers = workers
        self._stop_flag = False

        self.history = []            # 记录每一次反应执行
        self.snapshots = []          # 每个 pass 结束时的 pool 快照
        self.current_pass = 0


    def _compute_outputs(self, reaction: Reaction, consumed_inputs: Dict[str,int]) -> Dict[str,int]:
        if callable(reaction.outputs):
            return reaction.outputs(consumed_inputs, self.pool)
        else:
            return dict(reaction.outputs)

    def try_reserve_and_consume(self, reaction: Reaction) -> Optional[Dict[str,int]]:
        """
        尝试原子地判断并消耗 reaction.inputs。
        成功则返回 consumed_inputs（字典），失败返回 None。
        """
        with self.lock:
            # 检查是否足够
            for k, needed in reaction.inputs.items():
                if self.pool.get(k, 0) < needed:
                    return None
            # 足够则消耗
            for k, needed in reaction.inputs.items():
                self.pool[k] -= needed
                # 删除为0的键（保持整洁）
                if self.pool[k] == 0:
                    del self.pool[k]
            # 返回实际消耗的输入（拷贝）
            return dict(reaction.inputs)

    def produce_outputs(self, outputs: Dict[str,int]):
        with self.lock:
            for k, v in outputs.items():
                if v == 0:
                    continue
                self.pool[k] += v

    def worker(self, task_queue: 'queue.Queue[Reaction]', local_exec_flag: Dict[str, int]):
        while True:
            try:
                reaction = task_queue.get(timeout=0.1)
            except queue.Empty:
                return
            # 尝试执行一次（如果底物不够则跳过）
            consumed = self.try_reserve_and_consume(reaction)
            if consumed is not None:
                outs = self._compute_outputs(reaction, consumed)
                # 验证 outputs 是非负整数
                for kk, vv in outs.items():
                    if not (isinstance(vv, int) and vv >= 0):
                        raise ValueError(f"Reaction {reaction.name} produced invalid output {kk}:{vv}")
                self.produce_outputs(outs)
                self.exec_count[reaction.name] += 1
                local_exec_flag['count'] += 1

                # 新增：记录调用历史 ===
                with self.lock:
                    self.history.append({
                        "pass": self.current_pass,
                        "reaction": reaction.name,
                        "inputs": consumed,
                        "outputs": outs
                    })
            # 标记任务完成
            task_queue.task_done()

    def run_until_stable(self, max_passes: int = 200, verbose: bool = True):
        """
        主循环：
          每一“pass”中，将当前所有 reactions 入队（每个 reaction 入队一次），
          启动若干 worker 去抢占执行（worker 在内部会检查输入是否足够并执行一次或跳过）。
          当一次 pass 完成（队列耗尽）后，如果在该 pass 中没有任何反应执行过，则认为系统稳定，结束。
        注意：这样可以让产物在同一次 pass 中被下一个 pass 的生产者看到并被再次执行，
        loop 会继续，直至没有可执行反应或达到了 max_passes。
        """
        pass_no = 0
        while pass_no < max_passes:
            pass_no += 1
            task_q: queue.Queue = queue.Queue()
            # 将所有 reaction 入队（每次入队一次）
            for r in self.reactions:
                task_q.put(r)

            local_exec_flag = {'count': 0}  # 用于记录这一 pass 是否有任何反应被执行
            threads = []
            for _ in range(self.workers):
                t = threading.Thread(target=self.worker, args=(task_q, local_exec_flag))
                t.start()
                threads.append(t)

            # 等待队列清空 & 线程结束
            # 先等待所有任务被标记完成或不可取
            task_q.join()
            # 等待线程退出
            for t in threads:
                t.join(timeout=0.1)

            if verbose:
                with self.lock:
                    pool_snapshot = dict(self.pool)
                print(f"[pass {pass_no}] 执行反应次数本轮 = {local_exec_flag['count']}, 当前池: {pool_snapshot}")

            # 如果本轮没有任何反应执行，认为稳定，退出
            if local_exec_flag['count'] == 0:
                if verbose:
                    print("系统达到稳定（没有可执行的反应）。退出。")
                break
        else:
            print("达到最大 pass 限制，停止。")

    def summary(self):
        print("=== Summary ===")
        print("最终 pool:", dict(self.pool))
        print("每个反应的执行次数:", dict(self.exec_count))

    def plot_trajectory(self, substance: str):
        """
        绘制某个物质在模拟过程中数量的变化轨迹
        """
        x = list(range(1, len(self.snapshots)+1))
        y = [snap.get(substance, 0) for snap in self.snapshots]

        plt.figure(figsize=(6,4))
        plt.plot(x, y, marker='o')
        plt.xlabel("Pass")
        # plt.ylabel(f"{substance} 数量")
        # plt.title(f"{substance} 代谢轨迹")
        plt.ylabel(f"mol")
        plt.title(f"metabolic trajectory")
        plt.grid(True)
        # plt.show()
        plt.savefig(f'{substance}.png')


# ---------- helper: 解析脂肪酸碳数等 ----------
def parse_fatty_acid_label(label: str) -> Optional[int]:
    """
    支持的输入例如：
      '脂肪酸(C16)', '脂肪酸(C18)', '脂肪酸(Cn)'（若 n 不可解析则返回 None）
    返回碳数整数（例如 16）
    """
    m = re.search(r'\(C(\d+)\)', label)
    if m:
        return int(m.group(1))
    return None

# ---------- 定义 reactions ----------
reactions = []

# 1 糖原分解: 糖原(1) -> 葡萄糖(2)
reactions.append(Reaction(
    name="糖原分解",
    inputs={"糖原": 1},
    outputs={"葡萄糖": 2}
))

# 2 糖异生 (乳酸+ATP+GTP -> 葡萄糖)
reactions.append(Reaction(
    name="糖异生",
    inputs={"乳酸": 2, "ATP": 6, "GTP": 2},
    outputs={"葡萄糖": 1}
))

# 3 糖原合成
reactions.append(Reaction(
    name="糖原合成",
    inputs={"葡萄糖": 2, "UTP": 1},
    outputs={"糖原": 1}
))

# 4 糖酵解: 葡萄糖-> 丙酮酸2, ATP2, NADH2  (这里把 ATP 作为底物之一，按你给的式子)
reactions.append(Reaction(
    name="糖酵解",
    inputs={"葡萄糖": 1, "ATP": 2, "NAD+": 2},
    outputs={"丙酮酸": 2, "ATP": 2, "NADH": 2}
))

# 5 丙酮酸脱氢 -> 乙酰辅酶A etc
reactions.append(Reaction(
    name="丙酮酸脱氢",
    inputs={"丙酮酸": 2, "CoA": 2, "NAD+": 2},
    outputs={"乙酰辅酶A": 2, "NADH": 2, "FADH2": 2}
))

# 6 脂肪酸β氧化: 需要解析脂肪酸碳数
def beta_oxidation_outputs(consumed_inputs, pool):
    # consumed_inputs 例如 {"脂肪酸(C16)":1, "CoA":1} 或 {"脂肪酸(Cn)":1, "CoA":1}
    # 查出 input 名称中碳数
    fa_label = None
    for k in consumed_inputs.keys():
        if k.startswith("脂肪酸"):
            fa_label = k
            break
    if not fa_label:
        return {}
    n = parse_fatty_acid_label(fa_label)
    if n is None:
        # 如果没有提供碳数，默认当做 C16
        n = 16
    # outputs: 乙酰辅酶A: n/2, FADH2: n/2 -1, NADH: n/2 -1
    a = n // 2
    f = max(0, a - 1)
    nd = max(0, a - 1)
    return {"乙酰辅酶A": a, "FADH2": f, "NADH": nd}

reactions.append(Reaction(
    name="脂肪酸β氧化",
    inputs={"脂肪酸(Cn)": 1, "CoA": 1},  # 在系统中请用实际标签例如 "脂肪酸(C16)"
    outputs=beta_oxidation_outputs
))

# 7 脂肪酸合成: 乙酰辅酶A:8 -> 脂肪酸(C16):1, CO2:8, CoA:8
reactions.append(Reaction(
    name="脂肪酸合成",
    inputs={"乙酰辅酶A": 8, "ATP": 7, "NADPH": 14},
    outputs={"脂肪酸(C16)": 1, "CO2": 8, "CoA": 8}
))

# 8 胆固醇合成
reactions.append(Reaction(
    name="胆固醇合成",
    inputs={"乙酰辅酶A": 18, "NADPH": 16, "ATP": 9},
    outputs={"胆固醇": 1}
))

# 9 酮体生成 (4 * Acetyl-CoA -> acetoacetate, beta-hydroxybutyrate, acetone)
reactions.append(Reaction(
    name="酮体生成",
    inputs={"乙酰辅酶A": 4},
    outputs={"乙酰乙酸": 1, "β-羟丁酸": 1, "丙酮": 1}
))

# 10 转氨基反应: 氨基酸 -> α-酮酸 + 谷氨酸
reactions.append(Reaction(
    name="转氨基反应",
    inputs={"氨基酸": 1, "α-酮戊二酸": 1},
    outputs={"α-酮酸": 1, "谷氨酸": 1}
))

# 11 尿素循环
reactions.append(Reaction(
    name="尿素循环",
    inputs={"NH3": 2, "CO2": 1, "ATP": 3, "天冬氨酸": 1},
    outputs={"尿素": 1, "延胡索酸": 1}
))

# 12 糖异生氨基酸转化 (丙氨酸 -> 葡萄糖)
reactions.append(Reaction(
    name="糖异生氨基酸转化",
    inputs={"丙氨酸": 2, "ATP": 6},
    outputs={"葡萄糖": 1}
))

# 13 胆红素结合
reactions.append(Reaction(
    name="胆红素结合",
    inputs={"间接胆红素": 1, "UDP-葡萄糖醛酸": 2},
    outputs={"结合胆红素": 1}
))

# 14 胆汁排泄
reactions.append(Reaction(
    name="胆汁排泄",
    inputs={"结合胆红素": 1},
    outputs={"排泄胆红素": 1}
))

# 15 药物解毒
reactions.append(Reaction(
    name="药物解毒I/II相",
    inputs={"药物": 1, "UDP-葡萄糖醛酸": 1},
    outputs={"药物-葡萄糖醛酸结合物": 1}
))

# 16 维生素D羟化
reactions.append(Reaction(
    name="维生素D羟化",
    inputs={"维生素D3": 1},
    outputs={"25-羟基维生素D3": 1}
))

# 17 磷酸戊糖途径
reactions.append(Reaction(
    name="磷酸戊糖途径",
    inputs={"葡萄糖-6-磷酸": 1},
    outputs={"NADPH": 1}
))


# ---------- 示例与运行 ----------
if __name__ == "__main__":
    # 初始池：示例（可根据需要修改）
    initial = {
        "糖原": 2,
        "ATP": 50,
        "NAD+": 20,
        "CoA": 30,
        "葡萄糖-6-磷酸": 5,
        "NADPH": 2,
        "乳酸": 4,
        "GTP": 10,
        "UTP": 5,
        "脂肪酸(C16)": 2,
        "NH3": 10,
        "CO2": 10,
        "天冬氨酸": 5,
        "乙酰辅酶A": 2,
        "丙酮酸": 0,
        "丙氨酸": 4,
        "间接胆红素": 1,
        "UDP-葡萄糖醛酸": 3,
        "药物": 1,
        "维生素D3": 1,
    }

    sim = MetabolicSimulator(reactions=reactions, initial_pool=initial, workers=6)
    print("初始池:", dict(sim.pool))
    sim.run_until_stable(max_passes=100, verbose=True)
    sim.summary()

    # 查看调用记录
    for h in sim.history[:5]:  # 打印前5条
        print(h)

    # 绘制葡萄糖轨迹
    sim.plot_trajectory("葡萄糖-6-磷酸")
