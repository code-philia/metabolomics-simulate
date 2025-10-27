# liver_metabolism_sim.py

import ast
import re
from collections import defaultdict
import matplotlib.pyplot as plt


# =======================================
# Reaction 类
# =======================================
class Reaction:
    def __init__(self, name, reactants, products):
        """
        reactants: dict[str, float]
        products: dict[str, float] 或 lambda reactants -> dict
        """
        self.name = name
        self.reactants = reactants
        self.products = products

    def compute_products(self, current_reactants):
        if callable(self.products):
            return self.products(current_reactants)
        return self.products


# =======================================
# 工具函数
# =======================================
def extract_dynamic_var(reactants):
    """
    从反应物中提取动态变量 (如 Fatty_acid(Cn) -> n)
    返回字典，例如 {"n": 16}
    """
    vars_dict = {}
    for k, v in reactants.items():
        # 匹配括号里的变量
        m = re.search(r"\((.*?)\)", k)
        if m:
            inside = m.group(1)  # 例如 Cn
            if "n" in inside:
                vars_dict["n"] = v
    return vars_dict


def parse_value(v_str):
    """
    把产物/底物中的系数解析为 int 或 lambda
    """
    v_str = v_str.strip()
    if re.search(r"[n]", v_str):  # 动态表达式
        expr = v_str
        return lambda reactants: eval(expr, {}, extract_dynamic_var(reactants))
    else:
        return ast.literal_eval(v_str)


# =======================================
# 解析 Reaction 的函数
# =======================================
def parse_reaction_line(line):
    """
    解析一行反应式
    例如:
    {"Acyl-CoA": 1, "AMP": 1, "PPi": 1} = acyl_CoA_synthetase(input={"Fatty_acid(Cn)": 1, "ATP": 1, "CoA": 1})
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    m = re.match(r'(.+?)\s*=\s*(\w+)\(input=(.+)\)', line)
    if not m:
        raise ValueError(f"无法解析行: {line}")

    products_str, enzyme_name, reactants_str = m.groups()

    # 解析 reactants
    reactants = ast.literal_eval(reactants_str.strip())

    # 解析 products（允许 lambda）
    products_dict = {}
    prod_items = re.findall(r'(".*?"|\'.*?\')\s*:\s*([^,}]+)', products_str)
    for k_str, v_str in prod_items:
        k = ast.literal_eval(k_str)
        v = parse_value(v_str)
        products_dict[k] = v

    # 如果含有 lambda，整体包装
    if any(callable(v) for v in products_dict.values()):
        def make_lambda(prod_dict):
            return lambda r: {k: (v(r) if callable(v) else v)
                              for k, v in prod_dict.items()}
        products = make_lambda(products_dict)
    else:
        products = products_dict

    return Reaction(enzyme_name, reactants, products)


def load_reactions_from_txt(file_path):
    reactions = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            reaction = parse_reaction_line(line)
            if reaction:
                reactions.append(reaction)
    return reactions


# =======================================
# 模拟器
# =======================================
class LiverMetabolismSimulator:
    def __init__(self, reactions, initial_metabolites=None):
        self.reactions = reactions
        self.metabolites = defaultdict(float)
        if initial_metabolites:
            self.metabolites.update(initial_metabolites)
        self.history = []

    def step(self):
        changed = False
        for r in self.reactions:
            if all(self.metabolites.get(k, 0) >= v for k, v in r.reactants.items()):
                # 消耗底物
                for k, v in r.reactants.items():
                    self.metabolites[k] -= v
                # 生成产物
                products = r.compute_products(r.reactants)
                for k, v in products.items():
                    self.metabolites[k] += v
                self.history.append((r.name, dict(self.metabolites)))
                changed = True
        return changed

    def run(self, max_steps=1000):
        for _ in range(max_steps):
            if not self.step():
                break

    def plot_metabolite(self, name):
        values = [state.get(name, 0) for _, state in self.history]
        plt.plot(values)
        plt.title(f"Metabolic trajectory of {name}")
        plt.xlabel("Step")
        plt.ylabel(name)
        plt.savefig(f'{name}.png')

    def plot_all_metabolites(self):
        # 收集所有物质
        all_metabolites = set()
        for _, state in self.history:
            all_metabolites.update(state.keys())
        # 准备数据
        data = {met: [] for met in all_metabolites}
        for _, state in self.history:
            for met in all_metabolites:
                data[met].append(state.get(met, 0))
        # 绘图
        plt.figure(figsize=(12, 6))
        for met, values in data.items():
            plt.plot(values, label=met)
        plt.title("Metabolic trajectories of all metabolites")
        plt.xlabel("Step")
        plt.ylabel("Concentration / Amount")
        plt.legend(loc='upper right', fontsize=8)
        plt.tight_layout()
        plt.savefig(f'history.png')



# =======================================
# 示例
# =======================================
if __name__ == "__main__":
    reactions = load_reactions_from_txt("metabolism_reactions.txt")

    simulator = LiverMetabolismSimulator(
        reactions,
        initial_metabolites={
            "Fatty_acid(C16)": 16,
            "ATP": 50,
            "NAD+": 20,
            "CoA": 30,
            "Glucose-6P": 5,
            "NADPH": 2,
            "Lactate": 4,
            "GTP": 10,
            "UTP": 5,
            "NH3": 10,
            "CO2": 10,
            "Asp": 5,
            "Acetyl-CoA": 2,
            "Pyruvate": 0,
            "Ala": 4,
            "Unconjugated Bilirubin": 1,
            "UDP-Glucose": 3,
        }
    )
    simulator.run()

    # 查看调用记录
    # for h in simulator.history:
    #     print(h)

    simulator.plot_all_metabolites()
