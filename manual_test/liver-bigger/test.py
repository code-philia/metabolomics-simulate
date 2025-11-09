# 我将执行并展示可以运行的完整 Python 代码：构建代谢网络类、反应（转换函数）、字典输出、数值模拟到稳态、并为每个代谢物单独绘图，最后把所有小图合成为一个 PNG。
# 运行环境是内置的 Jupyter；运行后会在 data 下生成文件，可以下载。
# 请耐心等待代码执行并显示结果与文件链接。

import json
import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# 不使用 seaborn，遵守绘图规则；每个图独立生成并保存，再合并为单张 PNG。

# 1. 定义代谢物与转换（反应）结构
@dataclass
class Reaction:
    id: str
    name: str
    inputs: Dict[str, float]   # metabolite -> stoichiometry (positive means consumed)
    outputs: Dict[str, float]  # metabolite -> stoichiometry (positive means produced)
    k: float                   # rate constant (arbitrary unit, e.g., per minute)
    reversible: bool = False

    def rate(self, conc: Dict[str, float]) -> float:
        """简单质量作用定律：v = k * Π_i [S_i]^{stoich} (只对消耗物质计数)"""
        prod = 1.0
        for s, sto in self.inputs.items():
            # 若为多分子反应，使用幂次；避免0^0和负数
            c = max(conc.get(s, 0.0), 0.0)
            if c <= 0 and sto > 0:
                return 0.0
            prod *= c ** sto
        return self.k * prod

@dataclass
class MetabolicNetwork:
    metabolites: List[str]
    reactions: List[Reaction]
    inflows: Dict[str, float] = field(default_factory=dict)   # external input rates (units conc/min)
    outflows: Dict[str, float] = field(default_factory=dict)  # external removal rates (1/min proportional)

    def simulate(self, y0: Dict[str, float], t_max=200.0, dt=0.1):
        steps = int(t_max / dt) + 1
        times = np.linspace(0, t_max, steps)
        conc = {m: float(y0.get(m, 0.0)) for m in self.metabolites}
        history = np.zeros((len(times), len(self.metabolites)))
        for i, t in enumerate(times):
            history[i, :] = [conc[m] for m in self.metabolites]
            # 计算各反应速率
            rates = [r.rate(conc) for r in self.reactions]
            # 构造浓度变化 dC/dt
            dcdt = {m: 0.0 for m in self.metabolites}
            # 内源/外源输入
            for m, v_in in self.inflows.items():
                dcdt[m] += v_in
            # 比例性流出（first-order removal）
            for m, k_out in self.outflows.items():
                dcdt[m] -= k_out * conc.get(m, 0.0)
            # 反应贡献
            for r, v in zip(self.reactions, rates):
                for m, sto in r.inputs.items():
                    dcdt[m] -= sto * v
                for m, sto in r.outputs.items():
                    dcdt[m] += sto * v
            # 欧拉积分（可以改成 RK4，但欧拉足够演示平衡）
            for m in self.metabolites:
                conc[m] = max(conc[m] + dt * dcdt[m], 0.0)
        return times, history

# 2. 根据用户提供的路径列出代谢物与转换（用较简化的计量）
metabolites = [
    "Dietary_TAG", "Emulsified_TAG", "2-MAG", "FFA", "Dietary_Chol", "FC", "CE",
    "TAG", "Chylomicron", "Chylomicron_Remnant", "VLDL", "IDL", "LDL", "HDL", "ApoA_I",
    "Glycerol", "G3P", "FA", "Acyl_CoA", "Acetyl_CoA", "Ketone", "ATP", "Glucose", "DNL_FA",
    "Bile_Acid", "Conjugated_Bile_Acid", "Bile"
]

# 3. 构建反应集合（转换函数）
reactions = [
    Reaction("R_emuls", "乳化", {"Dietary_TAG":1.0}, {"Emulsified_TAG":1.0}, k=1.0),
    Reaction("R_lipase_intestinal", "胰脂肪酶水解", {"Emulsified_TAG":1.0}, {"2-MAG":1.0, "FFA":2.0}, k=0.8),
    Reaction("R_reesterify_intestine", "重酯化（肠）", {"2-MAG":1.0, "FFA":1.0}, {"TAG":1.0}, k=0.5),
    Reaction("R_chol_hydro", "胆固醇酯酶水解", {"Dietary_Chol":1.0}, {"FC":1.0}, k=0.6),
    Reaction("R_chol_esterify", "胆固醇酯化", {"FC":1.0}, {"CE":1.0}, k=0.4),
    Reaction("R_chylomicron_assembly", "乳糜微粒装配（ApoB48+MTP）", {"TAG":1.0, "CE":0.2}, {"Chylomicron":1.0}, k=0.3),
    Reaction("R_LPL_chyl", "LPL作用于乳糜微粒", {"Chylomicron":1.0}, {"2-MAG":0.5, "FFA":1.0, "Chylomicron_Remnant":1.0}, k=0.6),
    Reaction("R_FFA_transport", "FFA转运为FA（细胞摄取）", {"FFA":1.0}, {"FA":1.0}, k=0.7),
    Reaction("R_acs", "酰基CoA合成（ACS）", {"FA":1.0}, {"Acyl_CoA":1.0}, k=0.9),
    Reaction("R_beta_ox", "β-氧化", {"Acyl_CoA":1.0}, {"Acetyl_CoA":1.0}, k=0.8),
    Reaction("R_TCA", "TCA产生ATP", {"Acetyl_CoA":1.0}, {"ATP":10.0}, k=0.7),
    Reaction("R_ketogenesis", "酮体生成", {"FA":1.0}, {"Ketone":1.0}, k=0.2),
    Reaction("R_TAG_synth_g3p", "TAG合成（G3P途径）", {"Acyl_CoA":3.0, "G3P":1.0}, {"TAG":1.0}, k=0.4),
    Reaction("R_TAG_hydrolysis", "TAG水解（包括HSL）", {"TAG":1.0}, {"Glycerol":1.0, "FA":2.0}, k=0.5),
    Reaction("R_glycerol_kinase", "甘油激酶GK", {"Glycerol":1.0}, {"G3P":1.0}, k=0.6),
    Reaction("R_VLDL_assembly", "VLDL装配（ApoB100）", {"TAG":1.0}, {"VLDL":1.0}, k=0.25),
    Reaction("R_LPL_VLDL", "LPL作用于VLDL", {"VLDL":1.0}, {"IDL":1.0, "FFA":1.0}, k=0.5),
    Reaction("R_HL_IDL_to_LDL", "HL作用 IDL->LDL", {"IDL":1.0}, {"LDL":1.0}, k=0.4),
    Reaction("R_LDL_uptake", "LDLR介导LDL摄取", {"LDL":1.0}, {"FC":1.0}, k=0.6),
    Reaction("R_HDL_formation", "ApoA-I + FC -> HDL", {"ApoA_I":1.0, "FC":1.0}, {"HDL":1.0}, k=0.3),
    Reaction("R_LCAT", "LCAT在HDL上酯化胆固醇", {"HDL":1.0}, {"HDL":1.0, "CE":0.1}, k=0.2),
    Reaction("R_CETP", "CETP在VLDL-HDL间交换", {"VLDL":1.0, "HDL":1.0}, {"VLDL":1.0, "HDL":1.0}, k=0.05),
    Reaction("R_chyl_remnant_uptake", "乳糜残粒到肝", {"Chylomicron_Remnant":1.0}, {"FC":0.5}, k=0.4),
    Reaction("R_bile_synth", "胆固醇->初级胆汁酸", {"FC":1.0}, {"Bile_Acid":1.0}, k=0.1),
    Reaction("R_bile_conjug", "胆汁酸结合（胺）", {"Bile_Acid":1.0}, {"Conjugated_Bile_Acid":1.0}, k=0.2),
    Reaction("R_bile_secretion", "胆汁盐外排 -> 胆汁", {"Conjugated_Bile_Acid":1.0}, {"Bile":1.0}, k=0.3),
    Reaction("R_glucose_to_DNL", "葡萄糖->DNL产生脂肪酸", {"Glucose":1.0}, {"DNL_FA":1.0}, k=0.05),
    Reaction("R_DNL_to_FA", "DNL产生的前体转成FA", {"DNL_FA":1.0}, {"FA":1.0}, k=0.4),
    Reaction("R_glycolysis_to_AcCoA", "糖酵解->乙酰CoA", {"Glucose":1.0}, {"Acetyl_CoA":1.0}, k=0.6),
    Reaction("R_HDL_to_cholesterol", "SR-BI将HDL胆固醇交给肝/细胞", {"HDL":1.0}, {"FC":0.5}, k=0.2),
    # 简化血红素-胆红素-排泄链为一个流程
    Reaction("R_heme_to_UB", "血红素分解->间接胆红素", {"Glycerol":0.0}, {"Indirect_Bil":0.0}, k=0.0)  # 占位，不在本模型定量
]

# 去掉占位反应（无效）
reactions = [r for r in reactions if r.k > 0]

# 4. 添加输入/输出系统（肠道摄入和粪便/尿液/排泄）
inflows = {
    "Dietary_TAG": 0.5,   # 食物输入速率 (conc units per min)
    "Dietary_Chol": 0.05,
    "Glucose": 1.0
}
# 简单的外排：胆汁排出、胆固醇通过胆汁/胆固醇代谢外流、酮体被肾清除
outflows = {
    "Bile": 0.3,
    "Ketone": 0.05,
    "Chylomicron": 0.01,
    "VLDL": 0.01,
    "LDL": 0.005,
    "FFA": 0.02,
    "FA": 0.01,
    "TAG": 0.005,
    "FC": 0.01
}

network = MetabolicNetwork(metabolites=metabolites, reactions=reactions, inflows=inflows, outflows=outflows)

# 5. 初始浓度估计 (任意合理起始值，单位 arbitrary concentration)
y0 = {m: 0.1 for m in metabolites}
# 让某些物质起始略高
y0.update({"Glucose":5.0, "Dietary_TAG":1.0, "Dietary_Chol":0.1, "ApoA_I":0.05, "G3P":0.5})

# 6. 运行模拟
t_max = 500.0  # 足够长以接近稳态
dt = 0.5
times, history = network.simulate(y0, t_max=t_max, dt=dt)

# 7. 估算稳态（最后10%的时间点取平均）
cut = int(len(times)*0.9)
steady_means = {m: float(np.mean(history[cut:, idx])) for idx, m in enumerate(metabolites)}

# 8. 估算每一反应的平均速率（用稳态浓度代入）
steady_conc = steady_means.copy()
reaction_rates_steady = {r.id: float(r.rate(steady_conc)) for r in reactions}

# 9. 生成字典文件（JSON）：代谢物表与反应表
met_dict = {m: {"initial": float(y0.get(m,0.0)), "steady_state": steady_means[m]} for m in metabolites}
reac_dict = {}
for r in reactions:
    reac_dict[r.id] = {
        "name": r.name,
        "inputs": r.inputs,
        "outputs": r.outputs,
        "k": r.k,
        "steady_rate": reaction_rates_steady[r.id]
    }

data = {"metabolites": met_dict, "reactions": reac_dict}

os.makedirs("data/metabolic_sim", exist_ok=True)
with open("data/metabolic_sim/network_dictionary.json", "w") as f:
    json.dump(data, f, indent=2)

# 10. 绘图：为每个代谢物生成独立图像（单独 Figure），然后合并为一个 PNG 网格。
plot_files = []
for idx, m in enumerate(metabolites):
    fig, ax = plt.subplots(figsize=(6,3))
    ax.plot(times, history[:, idx])
    ax.set_title(m)
    ax.set_xlabel("time (min)")
    ax.set_ylabel("conc (a.u.)")
    ax.grid(True)
    fname = f"data/metabolic_sim/plot_{idx}_{m}.png"
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)
    plot_files.append(fname)

# 合并成网格
images = [Image.open(p) for p in plot_files]
n = len(images)
cols = int(math.ceil(math.sqrt(n)))
rows = int(math.ceil(n / cols))
# 先统一每张图片大小
w, h = images[0].size
margin = 10
grid_w = cols * w + (cols+1)*margin
grid_h = rows * h + (rows+1)*margin
grid_img = Image.new("RGB", (grid_w, grid_h), color=(255,255,255))

for i, im in enumerate(images):
    r = i // cols
    c = i % cols
    x = margin + c * (w + margin)
    y = margin + r * (h + margin)
    grid_img.paste(im, (x, y))

out_path = "data/metabolic_sim/all_metabolites_grid.png"
grid_img.save(out_path)

# 输出摘要信息
summary = {
    "dictionary_file": "data/metabolic_sim/network_dictionary.json",
    "combined_plot": out_path,
    "steady_state_sample": {k: steady_means[k] for k in list(steady_means)[:10]},  # 示范部分
    "reaction_rates_sample": {k: reaction_rates_steady[k] for k in list(reaction_rates_steady)[:10]}
}

with open("data/metabolic_sim/summary.json", "w") as f:
    json.dump(summary, f, indent=2)

# 列出生成的关键文件供下载
print("Files generated:")
for p in [summary["dictionary_file"], summary["combined_plot"], "data/metabolic_sim/summary.json"]:
    print(p)

# 呈现少量输出以便用户查看
summary, list(steady_means.items())[:12]
