import json
import math
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Callable
from PIL import Image
import os



# ====================================================
# Reaction Class (unchanged)
# ====================================================
@dataclass
class Reaction:
    id: str
    name: str
    inputs: Dict[str, float]
    outputs: Dict[str, float]

    # kinetics
    k_max: float
    Km: Dict[str, float]
    Hill: Dict[str, float]
    Ki: Dict[str, float]
    Ki_Hill: Dict[str, float]

    # environment
    pH_opt: float = 7.4
    sigma_pH: float = 1.0
    Q10: float = 2.0

    # transport
    transport_Vmax: float = 0.0
    transport_Km: float = 1.0

    # hormones & feedback
    hormone_factors: Dict[str, float] = field(default_factory=dict)
    feedback_params: Dict[str, Tuple[float, float]] = field(default_factory=dict)

    def rate(self, conc, hormones, env):
        # substrate term
        S_term = 1.0
        for s, sto in self.inputs.items():
            S = max(conc.get(s, 0), 0)
            Km = self.Km.get(s, 1.0)
            n = self.Hill.get(s, 1.0)
            S_term *= (S**n) / (Km**n + S**n)

        # product inhibition
        I_term = 1.0
        for p, Ki in self.Ki.items():
            P = max(conc.get(p, 0), 0)
            m = self.Ki_Hill.get(p, 1.0)
            I_term *= (Ki**m) / (Ki**m + P**m)

        # environment
        T = env.get("T", 37)
        Q10_term = self.Q10 ** ((T - 37) / 10)
        pH_factor = math.exp(-((env["pH"] - self.pH_opt) ** 2) / (2 * self.sigma_pH ** 2))

        # transport
        if self.transport_Vmax > 0:
            s = list(self.inputs.keys())[0]
            S = conc.get(s, 0)
            transport = self.transport_Vmax * S / (self.transport_Km + S)
        else:
            transport = 1.0

        # hormones
        hormone_term = 1.0
        for h, coef in self.hormone_factors.items():
            hormone_term *= (1 + coef * hormones.get(h, 0))

        # feedback
        fb = 1.0
        for x, (Ki, m) in self.feedback_params.items():
            X = conc.get(x, 0)
            fb *= Ki**m / (Ki**m + X**m)

        return self.k_max * S_term * I_term * Q10_term * pH_factor * transport * hormone_term * fb


# ====================================================
# Metabolic Network (now supports external input/output)
# ====================================================
class MetabolicNetwork:
    def __init__(
        self,
        reactions,
        initial_conc,
        food_input_fn: Callable[[float], Dict[str, float]] = None,
        waste_output_fn: Callable[[Dict[str, float]], Dict[str, float]] = None,
    ):
        self.reactions = reactions
        self.conc = initial_conc.copy()
        self.food_input_fn = food_input_fn
        self.waste_output_fn = waste_output_fn

        self.hormones = {"insulin": 1.0, "glucagon": 0.3}
        self.env = {"T": 37, "pH": 7.4}

    def simulate(self, dt=0.1, steps=500):
        conc_hist = []
        rate_hist = []

        for t in range(steps):
            rates = [r.rate(self.conc, self.hormones, self.env) for r in self.reactions]
            rate_hist.append(rates)

            # initialize Δ
            delta = {m: 0.0 for m in self.conc}

            # biochemical reactions
            for r, v in zip(self.reactions, rates):
                for s, sto in r.inputs.items():
                    delta[s] -= sto * v
                for p, sto in r.outputs.items():
                    delta[p] += sto * v

            # external food input (meal absorption curve)
            if self.food_input_fn:
                food = self.food_input_fn(t * dt)
                for m, flux in food.items():
                    delta[m] += flux

            # external waste excretion
            if self.waste_output_fn:
                waste = self.waste_output_fn(self.conc)
                for m, flux in waste.items():
                    delta[m] -= flux

            # update concentrations
            for m in self.conc:
                self.conc[m] = max(self.conc[m] + delta[m] * dt, 0)

            conc_hist.append(self.conc.copy())

        return conc_hist, rate_hist


# ====================================================
# Load reactions
# ====================================================
def load_reactions(path):
    with open(path, "r") as f:
        params = json.load(f)

    reactions = []
    for rid, p in params.items():
        reactions.append(
            Reaction(
                id=rid,
                name=p["name"],
                inputs=p["inputs"],
                outputs=p["outputs"],
                k_max=p["k_max"],
                Km=p["Km"],
                Hill=p["Hill"],
                Ki=p["Ki"],
                Ki_Hill=p["Ki_Hill"],
                pH_opt=p["pH_opt"],
                sigma_pH=p["sigma_pH"],
                Q10=p["Q10"],
                transport_Vmax=p["transport_Vmax"],
                transport_Km=p["transport_Km"],
                hormone_factors=p["hormone_factors"],
                feedback_params=p["feedback_params"],
            )
        )
    return reactions


# ====================================================
# Visualization
# ====================================================
def plot_metabolites(conc_hist, out_dir="metabolite_plots", grid_fname="history_metabolites_grid.png"):
    """
    为每个代谢物生成单独图像，然后自动合并成一个网格 PNG。
    """

    # 创建目录
    os.makedirs(out_dir, exist_ok=True)

    metabolites = list(conc_hist[0].keys())
    image_paths = []

    # === 1. 为每个代谢物单独创建图像 ===
    for m in metabolites:
        values = [c[m] for c in conc_hist]

        plt.figure(figsize=(4, 3))
        plt.plot(values)
        plt.title(m)
        plt.xlabel("Steps")
        plt.ylabel("Concentration")
        
        file_path = os.path.join(out_dir, f"{m}.png")
        plt.savefig(file_path, dpi=120, bbox_inches='tight')
        plt.close()
        
        image_paths.append(file_path)

    # === 2. 合并为一个网格图 ===

    imgs = [Image.open(p) for p in image_paths]

    N = len(imgs)
    cols = math.ceil(math.sqrt(N))
    rows = math.ceil(N / cols)

    # 获取单图大小
    w, h = imgs[0].size

    # 创建大画布
    grid = Image.new("RGB", (cols * w, rows * h), "white")

    # 放置每张小图
    for idx, img in enumerate(imgs):
        r = idx // cols
        c = idx % cols
        grid.paste(img, (c * w, r * h))

    # 保存最终网格图
    grid.save(grid_fname)
    print(f"Combined image saved to: {grid_fname}")


def plot_rates(rate_hist, reactions, fname='history_rate.png'):
    plt.figure(figsize=(16, 12))
    for i, r in enumerate(reactions):
        plt.plot([step[i] for step in rate_hist], label=r.id)
    plt.legend()
    plt.title("Reaction Rates")
    plt.xlabel("Steps")
    plt.ylabel("Rate")
    plt.show()
    plt.savefig(fname)


# ====================================================
# Default Meal Input and Waste Output
# ====================================================

def meal_input(t):
    """
    模拟吃一顿饭后 0–2 小时内 TAG、葡萄糖逐渐吸收入血的真实模型。
    """

    # 食物进入小肠的吸收动力学（正态分布 + 下降）
    def pulse(t, peak=30, width=20):
        return math.exp(-((t - peak) ** 2) / (2 * width ** 2))

    return {
        "Dietary_TAG": 5.0 * pulse(t * 60),      # 餐后 TAG
        "Glucose": 3.0 * pulse(t * 60),          # 餐后葡萄糖
        "FreeCholesterol": 0.5 * pulse(t * 60),      # 胆固醇
    }


def default_waste_output(conc):
    """
    模拟肝脏排泄：胆汁酸、乳糜微粒残粒。
    假设为简单的线性清除：flux = k_clear * conc
    """
    return {
        # "Chylomicron_Remnant": 0.02 * conc.get("Chylomicron_Remnant", 0),
        # "Bile_Acid": 0.05 * conc.get("Bile_Acid", 0),
        "Bile": 0.05 * conc.get("Bile", 0),
    }


# ====================================================
# Recommended Realistic Initial Conditions
# ====================================================
realistic_initial = {
    # 小肠 / 肝脏
    "Dietary_TAG": 0,
    "Emulsified_TAG": 0.1,
    "2-MAG": 0.05,
    "FFA": 0.2,

    # 血浆
    "FFA": 0.4,
    "FA": 0.5,
    "CoA": 0.2,
    "Acetyl_CoA": 0.3,

    # 能量状态
    "ATP": 1.5,
    "NADH": 0.5,

    # 脂蛋白
    "Chylomicron": 0.05,

    # 胆固醇相关
    "FreeCholesterol": 0.5,
    "CholesterylEster": 0.5,
    "Bile_Acid": 0.1,

    # 葡萄糖
    "Glucose": 5.0,

    # 胆红素系统
    "Bile": 0.1,
}

def build_initial_pool(reactions, user_initial=None, default_value=0.0):
    all_mets = set()
    for r in reactions:
        all_mets.update(r.inputs.keys())
        all_mets.update(r.outputs.keys())

    init = {m: default_value for m in all_mets}

    if user_initial:
        for m, v in user_initial.items():
            init[m] = v

    return init


# ====================================================
# Main Entry
# ====================================================
if __name__ == "__main__":
    reactions = load_reactions("reaction_parameters.json")

    initial_conc = build_initial_pool(reactions, user_initial=realistic_initial)
    # initial_conc = build_initial_pool(reactions, default_value=1.0)

    net = MetabolicNetwork(
        reactions,
        initial_conc,
        food_input_fn=meal_input,
        waste_output_fn=default_waste_output,
    )

    conc_hist, rate_hist = net.simulate(dt=0.1, steps=300)

    plot_metabolites(conc_hist)
    plot_rates(rate_hist, reactions)
