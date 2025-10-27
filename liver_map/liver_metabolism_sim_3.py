# liver_metabolism_sim.py
import re
from collections import defaultdict
from queue import Queue
import threading
import matplotlib.pyplot as plt

# =======================================
# Reaction 类
# =======================================
class Reaction:
    def __init__(self, reactants, name, product_func):
        """
        reactants: dict {metabolite_name: amount}
        name: str
        product_func: function, 根据输入反应物返回产物字典
        """
        self.reactants = reactants
        self.name = name
        self.compute_products = product_func

# =======================================
# 解析反应表字符串
# =======================================
def parse_reaction_line(line):
    """
    line 示例：
    {"Acyl-CoA": 1, "AMP": 1, "PPi": 1} = acyl_CoA_synthetase(input={"Fatty_acid(Cn)": 1, "ATP": 1, "CoA": 1})
    """
    lhs_rhs = line.split("=")
    if len(lhs_rhs) != 3:
        raise ValueError(f"Cannot parse line: {line}")
    # 产物
    products_str = lhs_rhs[0].strip()
    products = eval(products_str)
    # 反应函数和输入
    rhs = f'{lhs_rhs[1]}={lhs_rhs[2]}'.strip()
    m = re.match(r'(\w+)\(input=(.*)\)', rhs)
    if not m:
        raise ValueError(f"Cannot parse reaction function: {rhs}")
    name, inputs_str = m.groups()
    reactants = eval(inputs_str)

    # 如果产物中有 (Cn) 或 n/2 之类动态系数，用 lambda 表达式动态计算
    def product_func(inputs):
        prod = {}
        for k, v in products.items():
            if isinstance(v, str):
                # 动态表达式
                local_dict = {}
                local_dict.update(inputs)
                try:
                    val = eval(v, {}, local_dict)
                except Exception:
                    val = 1
            else:
                val = v
            prod[k] = val
        return prod

    return Reaction(reactants, name, product_func)

def parse_reactions_from_txt(filename):
    reactions = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                reactions.append(parse_reaction_line(line))
    return reactions

# =======================================
# 生产者-消费者模拟器
# =======================================
class ReactionThread(threading.Thread):
    def __init__(self, reaction, metabolite_pool, executed_queue, lock):
        super().__init__()
        self.reaction = reaction
        self.metabolite_pool = metabolite_pool
        self.executed_queue = executed_queue
        self.lock = lock

    def run(self):
        with self.lock:
            # 检查反应物是否足够
            if all(self.metabolite_pool.get(k, 0) >= v for k, v in self.reaction.reactants.items()):
                for k, v in self.reaction.reactants.items():
                    self.metabolite_pool[k] -= v
                products = self.reaction.compute_products(self.reaction.reactants)
                for k, v in products.items():
                    self.metabolite_pool[k] += v
                self.executed_queue.put(self.reaction.name)

class LiverMetabolismSimulatorPC:
    def __init__(self, reactions, initial_metabolites=None):
        self.reactions = reactions
        self.metabolites = defaultdict(float)
        if initial_metabolites:
            self.metabolites.update(initial_metabolites)
        self.history = []

    def step(self):
        lock = threading.Lock()
        executed_queue = Queue()
        threads = []

        for r in self.reactions:
            t = ReactionThread(r, self.metabolites, executed_queue, lock)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        executed_this_step = []
        while not executed_queue.empty():
            executed_this_step.append(executed_queue.get())

        if executed_this_step:
            self.history.append({
                'executed_reactions': executed_this_step,
                'metabolites': dict(self.metabolites)
            })
            return True
        return False

    def run(self, max_steps=100):
        for _ in range(max_steps):
            if not self.step():
                break

    def print_execution_history(self):
        for i, record in enumerate(self.history):
            print(f"Step {i+1}:")
            print("  Executed reactions:", ", ".join(record['executed_reactions']))
            print("  Metabolites:", record['metabolites'])
            print("-" * 50)

    def plot_all_metabolites(self):
        all_metabolites = set()
        for state in self.history:
            all_metabolites.update(state['metabolites'].keys())
        data = {met: [] for met in all_metabolites}
        for state in self.history:
            for met in all_metabolites:
                data[met].append(state['metabolites'].get(met, 0))
        plt.figure(figsize=(12, 6))
        for met, values in data.items():
            plt.plot(values, label=met)
        plt.title("Metabolic trajectories of all metabolites")
        plt.xlabel("Step")
        plt.ylabel("Concentration / Amount")
        plt.legend(loc='upper right', fontsize=8)
        plt.tight_layout()
        plt.savefig('history.png')

# =======================================
# 示例：摄入乳糖和脂肪
# =======================================
if __name__ == "__main__":
    # 定义部分反应（从txt导入）
    reactions = parse_reactions_from_txt('./metabolism_reactions_simple.txt')

    # 初始代谢物
    initial_metabolites = {
        "Lactose": 2,
        "Fatty_acid(C16)": 2,
        "ATP": 20,
        "UTP": 5,
        "CoA": 10,
        "NADPH": 20,
        "(Glycogen)n": 0
    }

    # # 初始代谢物
    # initial_metabolites={
    #     "Fatty_acid(C16)": 16,
    #     "ATP": 50,
    #     "NAD+": 20,
    #     "CoA": 30,
    #     "Glucose-6P": 5,
    #     "NADPH": 2,
    #     "Lactate": 4,
    #     "GTP": 10,
    #     "UTP": 5,
    #     "NH3": 10,
    #     "CO2": 10,
    #     "Asp": 5,
    #     "Acetyl-CoA": 2,
    #     "Pyruvate": 0,
    #     "Ala": 4,
    #     "Unconjugated Bilirubin": 1,
    #     "UDP-Glucose": 3,
    # }

    # multi = 10
    # for k, v in initial_metabolites.items():
    #     initial_metabolites[k] = v * multi

    simulator = LiverMetabolismSimulatorPC(reactions, initial_metabolites)
    simulator.run(max_steps=20)
    simulator.print_execution_history()
    simulator.plot_all_metabolites()
