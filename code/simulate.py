import numpy as np
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor


class MetabolicEnvironment:
    def __init__(self):
        self.metabolites = {
            # --- 糖代谢 (mmol/L) ---
            "glucose": 4.5,            # 正常空腹血糖 3.9-6.1 mmol/L
            "g6p": 0.1,                # 葡萄糖-6-磷酸 (中间缓冲池)
            "f16bp": 0.1,
            "glycogen": 400.0,         # 肝糖原储备，约 100-120g，此处设定为储备浓度单位
            "pyruvate": 0.1,           # 丙酮酸正常水平较低 (0.05-0.2)
            "lactate": 1.0,            # 正常乳酸 < 2.0 mmol/L

            # --- 脂代谢 (mmol/L) ---
            "fatty_acid": 0.5,         # 游离脂肪酸 0.2-0.6 mmol/L
            "triglycerides": 1.5,      # 甘油三酯 < 1.7 mmol/L
            "glycerol": 0.1,           # 甘油正常水平
            "cholesterol": 4.5,        # 总胆固醇 3.1-5.2 mmol/L
            "bile_acid": 0.005,        # 血清胆汁酸极低，主要在胆囊循环

            # --- 蛋白质与氮代谢 (mmol/L) ---
            "amino_acid": 25.0,         # 总氨基酸水平
            "ammonia": 0.3,           # 血氨极低 (0.01-0.06)，高了会中毒
            "urea": 4.0,               # 尿素氮 2.5-7.1 mmol/L
            "albumin": 0.12,            # 约 40g/L，换算摩尔浓度约为 0.6 mmol/L
            "clotting_factor": 1.0,    # 相对活性单位

            # --- 能量与辅酶 (肝细胞内估计浓度 mmol/L) ---
            "atp": 3.5,                # 胞内 ATP 浓度 2-5 mmol/L
            "adp": 0.4,                # ATP/ADP 比例通常维持在 5-10
            "nad_plus": 0.6,           # 辅酶池总浓度在 0.5-1.0 左右
            "nadh": 0.005,              # 正常态 NAD+/NADH 比例约为 10:1
            "nadph": 0.3,              # 主要用于合成，浓度较稳定
            "acetyl_coa": 0.01,        # 关键中间产物，流转极快，浓度极低
            "ketone_body": 0.1,        # 非饥饿状态极低

            # --- 氧化还原与解毒 (mmol/L) ---
            "gsh": 5.0,                # 还原型谷胱甘肽是肝脏主打，浓度较高
            "udpga": 0.5,              # 葡萄糖醛酸供体
            "paps": 0.03,               # 硫酸化供体
            "indirect_bilirubin": 0.01,# 正常总胆红素 < 0.02
            "direct_bilirubin": 0.002,
            "oxygen": 5.0,             # 肝静脉/组织供氧水平

            # --- 辅酶再生原料 (μmol/L 级别，设为 mmol 匹配单位) ---
            "nicotinamide": 0.05,
            "niacin": 0.02,
            "tryptophan": 0.08,

            # --- 酒精代谢相关 (初始为 0) ---
            "ethanol": 0.0,
            "acetaldehyde": 0.0,
            "acetate": 0.0,
            "phaseI_intermediates": 0.0,
            "conjugates": 0.0,
            "napqi": 0.0,

            # --- 尿素循环中间体 (mmol/L) ---
            "ornithine": 0.1,
            "citrulline": 0.03,
            "argininosuccinate": 0.01,
            "arginine": 0.1
        }
        self.signals = {
            "insulin": 0.5,
            "glucagon": 0.5,
            "epinephrine": 0.1,
            "cortisol": 0.1,
            "inflammation": 0.0
        }
        self.parameters = {
            "oxygen_pressure": 100.0,
            "pH": 7.4,
            "temperature": 37.0,
            "is_postprandial": False,
            "insulin_degrading_enzyme_activity": 1.0,
            "liver_function": 1.0,
            "xenobiotic_load": 0.0,
            "insulin_sensitivity": 1.0,
            "aldh_activity": 1.0
        }
        self.history = []
        self.current_rates = {}

    def update_history(self, t):
        rate_fields = {f"rate_{k}": float(v) for k, v in self.current_rates.items()}
        record = {**self.metabolites, **self.signals, **self.parameters, **rate_fields, "time": t}
        self.history.append(record)
        self.current_rates.clear()

    def getMetabolite(self, name: str, compartment: str = None) -> float:
        return float(self.metabolites.get(name, 0.0))

    def setMetabolite(self, name: str, value: float, compartment: str = None) -> None:
        self.metabolites[name] = float(max(value, 0.0))

    def getSignal(self, name: str) -> float:
        return float(self.signals.get(name, 0.0))

    def setSignal(self, name: str, value: float) -> None:
        self.signals[name] = float(max(value, 0.0))

    def getParameter(self, name: str) -> float:
        return float(self.parameters.get(name, 0.0))

    def setParameter(self, name: str, value: float) -> None:
        self.parameters[name] = float(value)

    def writeOutputs(self, outputs: Dict[str, float]) -> None:
        for k, v in outputs.items():
            self.metabolites[k] = float(max(self.metabolites.get(k, 0.0) + float(v), 0.0))
    
    def recordRate(self, name: str, rate: float) -> None:
        self.current_rates[name] = float(rate)


class Ctx:
    def __init__(self, env: MetabolicEnvironment):
        self.env = env
        self.rate_modifier = 1.0
        self.last_outputs: Dict[str, Any] = {}

    def control(self, ccId: str) -> bool:
        if ccId == "postprandial":
            return bool(self.env.getParameter("is_postprandial"))
        return True

    def applyAction(self, action: str, payload: Any = None) -> None:
        if action == "downscale_rates":
            self.rate_modifier = float(payload) if payload is not None else 0.5

    def write(self, outputs: Dict[str, float]) -> None:
        self.env.writeOutputs(outputs)
        self.last_outputs = outputs

class ResourcePool:
    def __init__(self, env: MetabolicEnvironment):
        self.snapshot_metabolites = dict(env.metabolites)
        self.snapshot_signals = dict(env.signals)
        self.snapshot_parameters = dict(env.parameters)
        self.outputs: Dict[str, float] = {}
        self.signal_updates: Dict[str, float] = {}
        self.rates: Dict[str, float] = {}
        self.lock = None
        import threading
        self.lock = threading.Lock()

    def write_output(self, outputs: Dict[str, float]) -> None:
        with self.lock:
            for k, v in outputs.items():
                self.outputs[k] = self.outputs.get(k, 0.0) + float(v)

    def set_signal(self, name: str, value: float) -> None:
        with self.lock:
            self.signal_updates[name] = float(max(value, 0.0))

    def set_metabolite_abs(self, name: str, new_value: float) -> None:
        base = float(self.snapshot_metabolites.get(name, 0.0))
        delta = float(max(new_value, 0.0)) - base
        with self.lock:
            self.outputs[name] = self.outputs.get(name, 0.0) + delta
    
    def record_rate(self, name: str, rate: float) -> None:
        with self.lock:
            self.rates[name] = float(rate)

    def drain(self) -> Dict[str, Dict[str, Any]]:
        with self.lock:
            out = {"metabolites": dict(self.outputs), "signals": dict(self.signal_updates), "rates": dict(self.rates)}
            self.outputs.clear()
            self.signal_updates.clear()
            self.rates.clear()
            return out

class ResourceEnv(MetabolicEnvironment):
    def __init__(self, pool: ResourcePool):
        super().__init__()
        self.pool = pool
        self.metabolites = pool.snapshot_metabolites
        self.signals = pool.snapshot_signals
        self.parameters = pool.snapshot_parameters
        self.history = []

    def update_history(self, t):
        pass

    def setMetabolite(self, name: str, value: float, compartment: str = None) -> None:
        self.pool.set_metabolite_abs(name, float(value))

    def setSignal(self, name: str, value: float) -> None:
        self.pool.set_signal(name, float(value))

    def writeOutputs(self, outputs: Dict[str, float]) -> None:
        self.pool.write_output(outputs)
    
    def recordRate(self, name: str, rate: float) -> None:
        self.pool.record_rate(name, rate)

def oxygen_supply(ctx: Ctx) -> Dict[str, float]:
    current_o2 = ctx.env.getMetabolite("oxygen")
    target_o2 = 5.0  # 假设正常肝脏氧浓度水平
    # 模拟从血液扩散，浓度越低补充越快
    supply_rate = 0.5 * (target_o2 - current_o2) 
    return {"oxygen": supply_rate}

def hexokinase_step(ctx: Ctx) -> Dict[str, float]:
    glucose = ctx.env.getMetabolite("glucose")
    atp = ctx.env.getMetabolite("atp")
    insulin = ctx.env.getSignal("insulin")
    # 肝脏葡萄糖激酶 (GK) 的 Km 较高，受胰岛素高度诱导
    v_max = 0.25  # 从 0.3 降低到 0.25
    km_glucose = 5.0 
    # 速率受血糖和胰岛素共同驱动
    rate = v_max * (glucose / (glucose + km_glucose)) * (0.2 + 0.8 * insulin)
    actual_rate = min(rate, glucose * 0.1, atp * 0.5)
    ctx.env.recordRate("hexokinase", actual_rate)
    return {"glucose": -actual_rate, "g6p": actual_rate, "atp": -actual_rate, "adp": actual_rate}

def pgm_G6P_to_G1P(ctx: Ctx) -> Dict[str, float]:
    g6p = ctx.env.getMetabolite("g6p")
    ins = ctx.env.getSignal("insulin")
    # 1. 动力学设计：PGM 是双向酶，但在合成路径中，它受胰岛素间接驱动
    # 我们设定一个合理的 Vmax，并使用米氏方程防止底物抽干
    v_max = 0.5 
    km_g6p = 0.5
    # 2. 只有当胰岛素存在时，糖原合成路径才活跃
    # 这样可以避免在饥饿状态下 G6P 浪费在合成路径上
    activation = ins / (ins + 0.2) 
    # 3. 计算速率：基础速率 * 饱和度 * 激活度
    rate = v_max * (g6p / (g6p + km_g6p)) * activation
    # 安全保护：单步消耗不超过现有底物的 20%
    actual_rate = min(rate, g6p * 0.2)
    ctx.env.recordRate("pgm_G6P_to_G1P", actual_rate)
    # 4. 返回 G6P 的消耗和中间体 G1P 的产生
    # 注意：后续的 udpGlucoseSynthesis 应该消耗这里产生的 g1p
    return {
        "g6p": -actual_rate, 
        "g1p": actual_rate  # 产生的 G1P 供下一步使用
    }

def udpGlucoseSynthesis(ctx: Ctx) -> Dict[str, float]:
    g1p = ctx.env.getMetabolite("g1p")
    atp = ctx.env.getMetabolite("atp")
    # 动力学：依赖 G1P 供应，且需要能量
    v_max = 0.5
    rate = v_max * (g1p / (g1p + 0.1)) * (atp / (atp + 0.2))
    # 安全保护
    actual_rate = min(rate, g1p * 0.5, atp * 0.2)
    ctx.env.recordRate("udpGlucoseSynthesis", actual_rate)
    return {
        "g1p": -actual_rate, 
        "udpg": actual_rate,  # 产生中间体 UDP-Glucose
        "atp": -actual_rate * 1.0, # 每步消耗 1 个高能磷酸键
        "adp": actual_rate * 1.0
    }

def glycogenSynthaseStep(ctx: Ctx) -> Dict[str, float]:
    ins = ctx.env.getSignal("insulin")
    udpg = ctx.env.getMetabolite("udpg")
    # 胰岛素开关：低于 0.3 基本不活跃
    activation = 1.0 / (1.0 + np.exp(-10.0 * (ins - 0.4)))
    v_max = 0.6
    rate = v_max * (udpg / (udpg + 0.5)) * activation
    actual_rate = min(rate, udpg * 0.8)
    ctx.env.recordRate("glycogenSynthaseStep", actual_rate)
    return {
        "udpg": -actual_rate,
        "glycogen": actual_rate # 碳原子最终进入糖原池
    }

def branchingEnzymeStep(ctx: Ctx) -> Dict[str, float]:
    # 在简化模型中，分支酶维持糖原结构的可用性
    # 我们可以设定它消耗极少量 ATP 来维持生物化学模拟的严谨性
    glycogen = ctx.env.getMetabolite("glycogen")
    rate = 0.01 * (glycogen / (glycogen + 100.0))
    ctx.env.recordRate("branchingEnzymeStep", rate)
    return {"atp": -rate * 0.1, "adp": rate * 0.1} # 仅产生微量能耗

def glycogenPhosphorylaseStep(ctx: Ctx) -> Dict[str, float]:
    glucagon = ctx.env.getSignal("glucagon")
    ep = ctx.env.getSignal("epinephrine")
    glycogen = ctx.env.getMetabolite("glycogen")
    v_max = 0.8  # 略微调高 Vmax，因为它是分解的主力
    km_glycogen = 100.0 
    # 逻辑：基础活性 + 激素激活
    activation = (0.05 + 0.6 * glucagon + 0.4 * ep)
    activation = min(activation, 1.2) # 强刺激下可以略超基准
    rate = (v_max * glycogen / (km_glycogen + glycogen)) * activation
    actual_rate = min(rate, glycogen * 0.05) # 提高单步最大分解比例，增强饥饿响应
    ctx.env.recordRate("glycogenPhosphorylaseStep", actual_rate)
    return {"glycogen": -actual_rate, "g1p": actual_rate}

def debranchingEnzymeStep(ctx: Ctx) -> Dict[str, float]:
    glycogen = ctx.env.getMetabolite("glycogen")
    glc = ctx.env.getSignal("glucagon")
    # 受胰高血糖素激活
    activation = glc / (glc + 0.5)
    rate = 0.1 * (glycogen / (glycogen + 50.0)) * activation
    ctx.env.recordRate("debranchingEnzymeStep", rate)
    # 糖原脱支：大部分变成 G1P 的前体，小部分（10%）直接变成葡萄糖
    return {
        "glycogen": -rate,
        "glucose": rate * 0.1, 
        "g1p": rate * 0.9
    }

def g1p_to_g6p(ctx: Ctx) -> Dict[str, float]:
    g1p = ctx.env.getMetabolite("g1p")
    # 这是一个平衡反应，方向通常由 g1p 的堆积驱动
    v_max = 1.0 
    rate = v_max * (g1p / (g1p + 0.1))
    actual_rate = min(rate, g1p * 0.9)
    ctx.env.recordRate("g1p_to_g6p", actual_rate)
    return {
        "g1p": -actual_rate,
        "g6p": actual_rate
    }

def pepck_OAA_to_PEP(ctx: Ctx) -> Dict[str, float]:
    atp = ctx.env.getMetabolite("atp")
    rate = ctx.rate_modifier * min(atp, 2.0) * 0.02
    ctx.env.recordRate("pepck_OAA_to_PEP", rate)
    return {"atp": -rate, "adp": rate}

def g6pase_G6P_to_Glucose(ctx: Ctx) -> Dict[str, float]:
    g6p = ctx.env.getMetabolite("g6p")
    ins = ctx.env.getSignal("insulin")
    # 胰岛素的强力钳制逻辑
    # 当胰岛素 > 0.2 时，闸门几乎完全关闭
    gate_open = 1.0 / (1.0 + np.exp(10.0 * (ins + 0.2)))
    v_max = 1.0 
    km = 0.5
    rate = v_max * (g6p / (g6p + km)) * gate_open
    outputs = {"g6p": -rate, "glucose": rate}
    ctx.write(outputs)
    ctx.env.recordRate("g6pase_G6P_to_Glucose", rate)
    return outputs

def pfk1_step(ctx: Ctx) -> Dict[str, float]:
    g6p = ctx.env.getMetabolite("g6p")
    atp = ctx.env.getMetabolite("atp")
    # 增加反馈抑制：除了 ATP 抑制，如果 F16BP 已经堆积了，也抑制 PFK1
    f16bp = ctx.env.getMetabolite("f16bp")
    product_inhibition = 1.0 / (1.0 + (f16bp / 0.5))
    # 生理反馈：ATP 是 PFK-1 的异构抑制剂
    # 当 ATP 充足时（>3.0），抑制糖酵解流量
    energy_inhibition = 1.0 / (1.0 + max(0, atp - 3.0) * 2.0)
    v_max = 0.2
    km_g6p = 0.2  # 低 Km 确保 G6P 能被有效向下游拉动
    rate = v_max * (g6p / (g6p + km_g6p)) * energy_inhibition * product_inhibition
    actual_rate = min(rate, g6p, atp * 0.5)
    ctx.env.recordRate("pfk1", actual_rate)
    # 此处产生一个虚拟的下游中间体 'f16bp' 或直接导向 'pep'
    return {"g6p": -actual_rate, "f16bp": actual_rate, "atp": -actual_rate, "adp": actual_rate}

def pyruvate_kinase_step(ctx: Ctx) -> Dict[str, float]:
    f16bp = ctx.env.getMetabolite("f16bp")
    adp = ctx.env.getMetabolite("adp")
    nad_plus = ctx.env.getMetabolite("nad_plus")
    # 1. 理论速率计算 - 进一步降低最大速率防止震荡
    v_max = 0.4  # 从0.5进一步降低到0.4
    # 引入 ADP 需求驱动，但使用更平缓的响应
    potential_rate = v_max * (f16bp / (f16bp + 0.4)) * (adp / (adp + 0.4)) * (nad_plus / (nad_plus + 0.15))
    # 2. 核心平滑逻辑：单步消耗率限制，进一步降低抽取比例
    # 确保 actual_rate 不会超过 f16bp 的 12%，也不会超过 adp 存量的 25%
    safe_factor = min(1.0, (f16bp * 0.12) / (potential_rate + 1e-6), (adp * 0.25) / (potential_rate * 4.0 + 1e-6))
    actual_rate = potential_rate * safe_factor * 0.85  # 从0.9降低到0.85阻尼因子
    ctx.env.recordRate("pyruvate_kinase", actual_rate)
    return {
        "f16bp": -actual_rate, 
        "pyruvate": actual_rate * 2.0, 
        "atp": actual_rate * 4.0, 
        "adp": -actual_rate * 4.0,
        "nad_plus": -actual_rate * 2.0,
        "nadh": actual_rate * 2.0
    }

def pyruvate_destination_logic(ctx: Ctx) -> Dict[str, float]:
    pyruvate = ctx.env.getMetabolite("pyruvate")
    oxygen = ctx.env.getMetabolite("oxygen")
    v_max = 0.5  # 从0.8降低到0.5
    # 基础速率 - 使用更平缓的米氏常数
    potential_rate = v_max * (pyruvate / (pyruvate + 0.8))  # 从0.5增加到0.8
    # 3. 核心平滑逻辑：降低抽取比例
    # 无论 v_max 多大，单步只消耗当前丙酮酸的 20% (从25%降低)
    actual_rate = potential_rate * min(1.0, (pyruvate * 0.2) / (potential_rate + 1e-6)) * 0.9  # 添加0.9阻尼因子
    # 使用更平缓的厌氧比例计算
    anaerobic_ratio = 1.0 / (1.0 + (oxygen / 15.0))  # 从10.0增加到15.0，更平缓
    lactate_rate = actual_rate * anaerobic_ratio
    aerobic_rate = actual_rate * (1.0 - anaerobic_ratio)
    ctx.env.recordRate("lactate_production", lactate_rate)
    return {
        "pyruvate": -actual_rate,
        "lactate": lactate_rate,
        "acetyl_coa": aerobic_rate,
        "nadh": -lactate_rate,# * 0.5,
        "nad_plus": lactate_rate# * 0.5 必须为1倍，与PK步的消耗平衡
    }

def fattyAcidSynthesis(ctx: Ctx) -> Dict[str, float]:
    insulin = ctx.env.getSignal("insulin")
    glucagon = ctx.env.getSignal("glucagon")
    ins_sens = ctx.env.getParameter("insulin_sensitivity")
    acetyl = ctx.env.getMetabolite("acetyl_coa")
    nadph = ctx.env.getMetabolite("nadph")
    atp = ctx.env.getMetabolite("atp")
    fa = ctx.env.getMetabolite("fatty_acid")
    lipogenesis_act = 1.0 / (1.0 + np.exp(-3.0 * (insulin - glucagon - 0.2)))
    synth_avail = 1.0 / (1.0 + np.exp(-3.0 * (1.0 - fa)))
    base = ctx.rate_modifier * (0.01 + 0.05 * insulin * ins_sens) * min(acetyl, nadph * 0.5, atp * 0.5)
    rate = base * lipogenesis_act * synth_avail * 0.8
    ctx.env.recordRate("fattyAcidSynthesis", rate)
    return {"acetyl_coa": -rate, "fatty_acid": rate, "nadph": -rate * 0.5, "atp": -rate * 0.2, "adp": rate * 0.2}

def betaOxidation(ctx: Ctx) -> Dict[str, float]:
    glucagon = ctx.env.getSignal("glucagon")
    insulin = ctx.env.getSignal("insulin")
    ep = ctx.env.getSignal("epinephrine")
    fa = ctx.env.getMetabolite("fatty_acid")
    nad_plus = ctx.env.getMetabolite("nad_plus")
    etoh = ctx.env.getMetabolite("ethanol")
    nadh = ctx.env.getMetabolite("nadh")
    alcohol_inhibition = 0.6 if (etoh > 0.5) else 1.0
    oxidation_act = 1.0 / (1.0 + np.exp(-3.0 * (glucagon - insulin - 0.2)))
    fa_supply = max(0.0, min(1.0, (fa - 0.3) / 2.0))
    base = ctx.rate_modifier * alcohol_inhibition * (0.3 + 0.4 * max(glucagon, ep)) * min(fa, nad_plus)
    rate = base * oxidation_act * max(0.3, fa_supply) * 1.2
    if fa > 4.0:
        rate *= 2.0
    elif fa > 2.0:
        rate *= 1.5
    ctx.env.recordRate("betaOxidation", rate)
    return {"fatty_acid": -rate, "acetyl_coa": rate, "nadh": rate, "nad_plus": -rate, "atp": rate * 0.5, "adp": -rate * 0.5}

def deNovoLipogenesis(ctx: Ctx) -> Dict[str, float]:
    insulin = ctx.env.getSignal("insulin")
    glucagon = ctx.env.getSignal("glucagon")
    ins_sens = ctx.env.getParameter("insulin_sensitivity")
    glucose = ctx.env.getMetabolite("glucose")
    atp = ctx.env.getMetabolite("atp")
    nadph = ctx.env.getMetabolite("nadph")
    fa = ctx.env.getMetabolite("fatty_acid")
    excess = max(0.0, (glucose - 4.0) / 4.0)
    lipogenesis_act = 1.0 / (1.0 + np.exp(-3.0 * (insulin - glucagon - 0.2)))
    synth_avail = 1.0 / (1.0 + np.exp(-3.0 * (1.0 - fa)))
    base = ctx.rate_modifier * (0.02 + 0.08 * insulin * ins_sens) * excess * min(glucose, atp * 0.5, nadph * 0.5)
    rate = base * lipogenesis_act * synth_avail * 0.8
    ctx.env.recordRate("deNovoLipogenesis", rate)
    return {"glucose": -rate, "fatty_acid": rate, "atp": -rate * 0.2, "adp": rate * 0.2, "nadph": -rate * 0.5}

def lipidTransport(ctx: Ctx) -> Dict[str, float]:
    insulin = ctx.env.getSignal("insulin")
    glucagon = ctx.env.getSignal("glucagon")
    ins_sens = ctx.env.getParameter("insulin_sensitivity")
    fa = ctx.env.getMetabolite("fatty_acid")
    tg = ctx.env.getMetabolite("triglycerides")
    lipogenesis_act = 1.0 / (1.0 + np.exp(-3.0 * (insulin - glucagon - 0.2)))
    base = ctx.rate_modifier * (0.01 + 0.05 * insulin * ins_sens) * min(fa, 5.0)
    rate = base * lipogenesis_act * 0.6
    tg_clear = -ctx.rate_modifier * 1.5 if tg > 1.5 * 1.8 else 0.0
    ctx.env.recordRate("lipidTransport", rate)
    return {"fatty_acid": -rate * 0.7, "triglycerides": rate + tg_clear}

def adiposeLipolysis(ctx: Ctx) -> Dict[str, float]:
    insulin = ctx.env.getSignal("insulin")
    glucagon = ctx.env.getSignal("glucagon")
    ep = ctx.env.getSignal("epinephrine")
    fa = ctx.env.getMetabolite("fatty_acid")
    oxidation_act = 1.0 / (1.0 + np.exp(-3.0 * (glucagon - insulin - 0.2)))
    drive = max(glucagon - insulin, 0.0) + ep * 1.0
    low_ins_boost = 0.5 if insulin < 0.2 else 0.0
    base = ctx.rate_modifier * (0.02 + 0.05 * (drive + low_ins_boost)) * 3.0
    rate = base * oxidation_act * 0.7
    ctx.env.recordRate("adiposeLipolysis", rate)
    fa_out = rate * 0.8
    if fa >= 1.5:
        fa_out *= 0.02
    return {"fatty_acid": fa_out, "glycerol": rate * 0.2}

def aminoAcidCatabolism(ctx: Ctx) -> Dict[str, float]:
    aa = ctx.env.getMetabolite("amino_acid")
    atp = ctx.env.getMetabolite("atp")
    cort = ctx.env.getSignal("cortisol")
    post = 1.0 if bool(ctx.env.getParameter("is_postprandial")) else 0.0
    rate = ctx.rate_modifier * (1.0 + 0.3 * post + 0.3 * cort) * min(max(aa - 20.0, 0.0), atp) * 0.05
    ctx.env.recordRate("aminoAcidCatabolism", rate)
    return {"amino_acid": -rate, "ammonia": rate, "atp": -rate * 0.1, "adp": rate * 0.1}

def aminoAcidSynthesisTransport(ctx: Ctx) -> Dict[str, float]:
    aa = ctx.env.getMetabolite("amino_acid")
    atp = ctx.env.getMetabolite("atp")
    rate = ctx.rate_modifier * min(aa, atp) * 0.005
    ctx.env.recordRate("aminoAcidSynthesisTransport", rate)
    return {"amino_acid": -rate, "albumin": rate * 0.6, "clotting_factor": rate * 0.4, "atp": -rate * 0.2, "adp": rate * 0.2}

def oxidativePhosphorylation(ctx: Ctx) -> Dict[str, float]:
    nadh = ctx.env.getMetabolite("nadh")
    oxygen = ctx.env.getMetabolite("oxygen")
    adp = ctx.env.getMetabolite("adp")
    # 修改：必须受到 ADP 的严格限制
    rate = ctx.rate_modifier * min(nadh, oxygen * 0.2, adp) * 1.5
    ctx.env.recordRate("oxidativePhosphorylation", rate)
    return {"nadh": -rate, "nad_plus": rate, "oxygen": -rate * 0.5, "atp": rate, "adp": -rate}

def ketogenesis(ctx: Ctx) -> Dict[str, float]:
    # 酮体生成
    glucose = ctx.env.getMetabolite("glucose")
    acetyl = ctx.env.getMetabolite("acetyl_coa")
    glucagon = ctx.env.getSignal("glucagon")
    insulin = ctx.env.getSignal("insulin")
    low_ins_gain = max(0.0, 1.0 - insulin)
    post = 1.0 if bool(ctx.env.getParameter("is_postprandial")) else 0.0
    post_clamp = 0.3 if post > 0.0 else 1.0
    rate = ctx.rate_modifier * post_clamp * (0.1 + 0.15 * glucagon + 0.12 * low_ins_gain) * max(0.0, (70.0 - glucose) / 70.0) * min(acetyl, 5.0)
    rate = max(min(rate, 0.15), 0.02)
    ctx.env.recordRate("ketogenesis", rate)
    return {"acetyl_coa": -rate, "ketone_body": rate}

def lactateFermentation(ctx: Ctx) -> Dict[str, float]:
    pyr = ctx.env.getMetabolite("pyruvate")
    nadh = ctx.env.getMetabolite("nadh")
    nad_plus = ctx.env.getMetabolite("nad_plus")
    oxygen = ctx.env.getMetabolite("oxygen")
    # --- 改进 1: 缺氧触发器逻辑 ---
    # 使用平滑的 S 曲线：氧气越低，hypox_factor 越接近 1.0
    # 当 oxygen = 40 时，factor 约为 0.5；当 oxygen < 20 时，迅速升至接近 1.0
    hypox_factor = 1.0 / (1.0 + np.exp(0.2 * (oxygen - 30.0)))
    # --- 改进 2: 氧化还原压力触发器 ---
    # 如果 NADH/NAD+ 比例失衡（例如大于 0.1），也应触发回收机制
    redox_ratio = nadh / (nad_plus + 1e-6)
    redox_factor = redox_ratio / (redox_ratio + 0.1) # 比例越高，系数越接近 1
    # 综合触发强度
    trig = max(hypox_factor, redox_factor)
    # --- 改进 3: 动力学计算 ---
    # v_max 适当调高，确保在危急时刻能快速回收 NAD+
    # 增加对丙酮酸的米氏常数限制，防止在丙酮酸几乎为 0 时过度抽取
    v_max = 0.5 
    potential_rate = v_max * (pyr / (pyr + 0.5)) * (nadh / (nadh + 0.2)) * trig
    # 安全限制：单步不要消耗超过当前丙酮酸或 NADH 的 30%
    actual_rate = potential_rate * min(1.0, (pyr * 0.3) / (potential_rate + 1e-6), (nadh * 0.3) / (potential_rate + 1e-6))
    ctx.env.recordRate("lactateFermentation", actual_rate)
    # 确保 1:1 回收
    return {
        "pyruvate": -actual_rate,
        "lactate": actual_rate,
        "nadh": -actual_rate,
        "nad_plus": actual_rate
    }

def nampt_Salvage(ctx: Ctx) -> Dict[str, float]:
    nam = ctx.env.getMetabolite("nicotinamide")
    atp = ctx.env.getMetabolite("atp")
    liver_fn = ctx.env.getParameter("liver_function")
    # 降低速率以防止 NAD+ 堆积
    rate = ctx.rate_modifier * min(nam, atp * 0.3) * 0.05 * liver_fn
    ctx.env.recordRate("nampt_Salvage", rate)
    return {"nicotinamide": -rate, "nad_plus": rate, "atp": -rate * 0.2, "adp": rate * 0.2}

def deNovoNADSynthesis(ctx: Ctx) -> Dict[str, float]:
    nia = ctx.env.getMetabolite("niacin")
    trp = ctx.env.getMetabolite("tryptophan")
    atp = ctx.env.getMetabolite("atp")
    liver_fn = ctx.env.getParameter("liver_function")
    precursor = min(nia + trp * 0.5, atp * 0.3)
    # 降低速率以防止 NAD+ 堆积
    rate = ctx.rate_modifier * precursor * 0.02 * liver_fn
    ctx.env.recordRate("deNovoNADSynthesis", rate)
    return {"niacin": -rate * 0.5, "tryptophan": -rate, "nad_plus": rate, "atp": -rate * 0.2, "adp": rate * 0.2}

def cps1_Ammonia_to_CarbamoylPhosphate(ctx: Ctx) -> Dict[str, float]:
    nh3 = ctx.env.getMetabolite("ammonia")
    atp = ctx.env.getMetabolite("atp")
    post = 1.0 if bool(ctx.env.getParameter("is_postprandial")) else 0.0
    rate = ctx.rate_modifier * (1.0 + 0.5 * post) * min(nh3, atp * 0.5) * 0.1
    ctx.env.recordRate("cps1_Ammonia_to_CarbamoylPhosphate", rate)
    return {"ammonia": -rate, "atp": -rate * 0.5, "adp": rate * 0.5, "citrulline": rate}

def otc_CarbamoylPhosphate_to_Citrulline(ctx: Ctx) -> Dict[str, float]:
    cit = ctx.env.getMetabolite("citrulline")
    orn = ctx.env.getMetabolite("ornithine")
    post = 1.0 if bool(ctx.env.getParameter("is_postprandial")) else 0.0
    rate = ctx.rate_modifier * (1.0 + 0.5 * post) * min(cit, orn) * 0.1
    ctx.env.recordRate("otc_CarbamoylPhosphate_to_Citrulline", rate)
    return {"citrulline": -rate, "argininosuccinate": rate}

def ass1_Citrulline_to_ASP_Argininosuccinate(ctx: Ctx) -> Dict[str, float]:
    arg_succ = ctx.env.getMetabolite("argininosuccinate")
    post = 1.0 if bool(ctx.env.getParameter("is_postprandial")) else 0.0
    rate = ctx.rate_modifier * (1.0 + 0.3 * post) * min(arg_succ, 5.0) * 0.08
    ctx.env.recordRate("ass1_Citrulline_to_ASP_Argininosuccinate", rate)
    return {"argininosuccinate": -rate, "arginine": rate}

def asl_Argininosuccinate_to_Arginine_Fumarate(ctx: Ctx) -> Dict[str, float]:
    arg = ctx.env.getMetabolite("arginine")
    post = 1.0 if bool(ctx.env.getParameter("is_postprandial")) else 0.0
    rate = ctx.rate_modifier * (1.0 + 0.3 * post) * min(arg, 5.0) * 0.08
    ctx.env.recordRate("asl_Argininosuccinate_to_Arginine_Fumarate", rate)
    return {"arginine": -rate, "urea": rate, "ornithine": rate * 0.5}

def arg1_Arginine_to_Urea_Ornithine(ctx: Ctx) -> Dict[str, float]:
    rate = 0.0
    ctx.env.recordRate("arg1_Arginine_to_Urea_Ornithine", rate)
    return {"urea": 0.0}

def phaseI_OxRed(ctx: Ctx) -> Dict[str, float]:
    xen = ctx.env.getParameter("xenobiotic_load")
    nadph = ctx.env.getMetabolite("nadph")
    liver_fn = ctx.env.getParameter("liver_function")
    rate = ctx.rate_modifier * min(xen, nadph) * 0.1 * liver_fn
    ctx.env.recordRate("phaseI_OxRed", rate)
    return {"phaseI_intermediates": rate, "nadph": -rate}

def phaseII_Conjugation(ctx: Ctx) -> Dict[str, float]:
    inter = ctx.env.getMetabolite("phaseI_intermediates")
    liver_fn = ctx.env.getParameter("liver_function")
    conj = ctx.env.getMetabolite("conjugates")
    udpga = ctx.env.getMetabolite("udpga")
    paps = ctx.env.getMetabolite("paps")
    gsh = ctx.env.getMetabolite("gsh")
    cof = max(0.0, min(udpga + paps + gsh, inter + 1.0))
    rate = ctx.rate_modifier * inter * 0.1 * (liver_fn ** 2) * (0.5 + 0.5 * min(cof / 10.0, 1.0))
    clear = ctx.rate_modifier * conj * 0.05 * max(liver_fn - 0.5, 0.0)
    ctx.env.recordRate("phaseII_Conjugation", rate)
    return {
        "phaseI_intermediates": -rate,
        "conjugates": rate - clear,
        "udpga": -rate * 0.2,
        "paps": -rate * 0.1,
        "gsh": -rate * 0.1,
    }

def bilirubinUGT(ctx: Ctx) -> Dict[str, float]:
    ib = ctx.env.getMetabolite("indirect_bilirubin")
    udpga = ctx.env.getMetabolite("udpga")
    liver_fn = ctx.env.getParameter("liver_function")
    rate = ctx.rate_modifier * min(ib, udpga * 0.5) * 0.05 * liver_fn
    ctx.env.recordRate("bilirubinUGT", rate)
    return {"indirect_bilirubin": -rate, "direct_bilirubin": rate, "udpga": -rate * 0.5}

def ethanol_ADH(ctx: Ctx) -> Dict[str, float]:
    etoh = ctx.env.getMetabolite("ethanol")
    nadp = ctx.env.getMetabolite("nad_plus")
    liver_fn = ctx.env.getParameter("liver_function")
    substrate_saturation = min(etoh / 1.0, 1.0)
    v_max = 1.5 * liver_fn
    cofactor_limit = min(1.0, nadp / 5.0)
    rate = ctx.rate_modifier * v_max * substrate_saturation * cofactor_limit
    ctx.env.recordRate("ethanol_ADH", rate)
    return {"ethanol": -rate, "acetaldehyde": rate, "nadh": rate * 0.8, "nad_plus": -rate * 0.8}

def acetaldehyde_ALDH(ctx: Ctx) -> Dict[str, float]:
    acald = ctx.env.getMetabolite("acetaldehyde")
    nadp = ctx.env.getMetabolite("nad_plus")
    liver_fn = ctx.env.getParameter("liver_function")
    aldh_act = ctx.env.getParameter("aldh_activity")
    substrate_saturation = min(acald / 1.0, 1.0)
    v_max = 1.2 * liver_fn * aldh_act
    cofactor_limit = min(1.0, nadp / 5.0)
    rate = ctx.rate_modifier * v_max * substrate_saturation * cofactor_limit
    ctx.env.recordRate("acetaldehyde_ALDH", rate)
    return {"acetaldehyde": -rate, "acetate": rate, "nadh": rate * 0.8, "nad_plus": -rate * 0.8}

def acetate_to_acetylcoa(ctx: Ctx) -> Dict[str, float]:
    ac = ctx.env.getMetabolite("acetate")
    atp = ctx.env.getMetabolite("atp")
    rate = ctx.rate_modifier * min(ac, atp * 0.5) * 0.1
    ctx.env.recordRate("acetate_to_acetylcoa", rate)
    return {"acetate": -rate, "acetyl_coa": rate, "atp": -rate * 0.2, "adp": rate * 0.2}

def bileAcidSynthesis(ctx: Ctx) -> Dict[str, float]:
    chol = ctx.env.getMetabolite("cholesterol")
    rate = ctx.rate_modifier * min(chol, 5.0) * 0.02
    ctx.env.recordRate("bileAcidSynthesis", rate)
    return {"cholesterol": -rate, "bile_acid": rate}

def plasmaProteinSynthesis(ctx: Ctx) -> Dict[str, float]:
    aa = ctx.env.getMetabolite("amino_acid")
    atp = ctx.env.getMetabolite("atp")
    post = 1.0 if bool(ctx.env.getParameter("is_postprandial")) else 0.0
    rate = ctx.rate_modifier * (1.0 + 0.5 * post) * min(aa, atp) * 0.005
    ctx.env.recordRate("plasmaProteinSynthesis", rate)
    return {"amino_acid": -rate, "albumin": rate, "atp": -rate * 0.2}

def coagulationFactorSynthesis(ctx: Ctx) -> Dict[str, float]:
    aa = ctx.env.getMetabolite("amino_acid")
    atp = ctx.env.getMetabolite("atp")
    rate = ctx.rate_modifier * min(aa, atp) * 0.01
    ctx.env.recordRate("coagulationFactorSynthesis", rate)
    return {"amino_acid": -rate, "clotting_factor": rate, "atp": -rate * 0.1}

def orchestrateGlycogenSynthesis(ctx: Ctx) -> Dict[str, float]:
    # 糖原合成 - 修复震荡问题
    ins = ctx.env.getSignal("insulin")
    glc = ctx.env.getSignal("glucagon")
    g6p = ctx.env.getMetabolite("g6p")
    atp = ctx.env.getMetabolite("atp")
    glycogen = ctx.env.getMetabolite("glycogen")
    
    # 调控逻辑：减少sigmoid陡峭度，添加滞后效应防止快速切换
    # 使用更平缓的sigmoid函数 (-5.0 而不是 -10.0)
    hormone_ratio = ins - glc
    activation = 1.0 / (1.0 + np.exp(-5.0 * (hormone_ratio - 0.45)))
    
    # 添加糖原浓度反馈抑制：当糖原水平高时，抑制合成
    glycogen_feedback = 1.0 / (1.0 + np.exp(3.0 * (glycogen - 600.0)))  # 600为抑制阈值
    
    # 动力学：依赖底物和能量，但降低最大速率
    v_max = 0.3  # 从0.5降低到0.3
    rate = v_max * (g6p / (g6p + 1.0)) * (atp / (atp + 0.5)) * activation * glycogen_feedback
    
    # 安全保护：单步不抽干，降低最大抽取比例
    actual_rate = min(rate, g6p * 0.15, atp * 0.08)  # 降低抽取比例
    
    ctx.env.recordRate("glycogen_synthesis_total", actual_rate)
    # 净反应：G6P + ATP -> Glycogen + ADP
    return {
        "g6p": -actual_rate,
        "glycogen": actual_rate,
        "atp": -actual_rate * 1.1, # 包含合成所需的 UTP/ATP 总能耗
        "adp": actual_rate * 1.1
    }

def orchestrateGlycogenBreakdown(ctx: Ctx) -> Dict[str, float]:
    # 糖原分解 - 修复震荡问题
    ins = ctx.env.getSignal("insulin")
    glc = ctx.env.getSignal("glucagon")
    ep = ctx.env.getSignal("epinephrine")
    glycogen = ctx.env.getMetabolite("glycogen")
    g6p = ctx.env.getMetabolite("g6p")
    
    # 调控逻辑：使用更平缓的sigmoid，添加G6P反馈抑制
    drive = max((glc - ins), ep)
    # 使用更平缓的sigmoid函数 (-5.0 而不是 -10.0)
    activation = 1.0 / (1.0 + np.exp(-5.0 * (drive - 0.45)))
    
    # 添加G6P反馈抑制：当G6P水平高时，抑制分解
    g6p_feedback = 1.0 / (1.0 + np.exp(-2.0 * (g6p - 8.0)))  # 8为抑制阈值
    
    # 动力学：受限于糖原总量，降低最大速率
    v_max = 0.3  # 从0.5降低到0.3
    rate = v_max * (glycogen / (glycogen + 50.0)) * activation * g6p_feedback
    
    # 安全保护：降低最大分解比例
    actual_rate = min(rate, glycogen * 0.04)  # 从0.05降低到0.04
    
    ctx.env.recordRate("glycogen_breakdown_total", actual_rate)
    # 净反应：Glycogen -> G6P (简化掉中间的 G1P)
    return {
        "glycogen": -actual_rate,
        "g6p": actual_rate
    }

def orchestrateGlycogen(ctx: Ctx) -> Dict[str, float]:
    o1 = orchestrateGlycogenSynthesis(ctx)
    o2 = orchestrateGlycogenBreakdown(ctx)
    outputs = {}
    for o in (o1, o2):
        for k, v in o.items():
            outputs[k] = outputs.get(k, 0.0) + v
    ctx.write(outputs)
    return outputs

def orchestrateGluconeogenesis(ctx: Ctx) -> Dict[str, float]:
    # 糖异生 - 修复震荡问题
    ins = ctx.env.getSignal("insulin")
    glc = ctx.env.getSignal("glucagon")
    # 核心调控：使用更平缓的sigmoid函数防止快速切换
    # 使用更平缓的sigmoid函数 (-3.0 而不是 -5.0)
    activation = 1.0 / (1.0 + np.exp(-3.0 * (glc - ins - 0.8)))
    # 只有当胰岛素极低且胰高血糖素高时，Vmax 才会释放，但降低最大速率
    v_max = 0.2 * activation  # 从0.3降低到0.2
    atp = ctx.env.getMetabolite("atp")
    # 糖异生极其耗能，ATP 不足时必须熄火
    atp_safety = max(0, (atp - 1.5) / 2.0)
    rate = v_max * atp_safety * 0.8  # 添加0.8阻尼因子
    outputs = {
        "g6p": rate, 
        "lactate": -rate * 0.4, 
        "glycerol": -rate * 0.3, 
        "amino_acid": -rate * 0.3, 
        "atp": -rate * 2.0,  # 真实生理：糖异生非常耗能
        "adp": rate * 2.0
    }
    ctx.write(outputs)
    ctx.env.recordRate("orchestrateGluconeogenesis", rate)
    return outputs

def orchestrateGlycolysis(ctx: Ctx) -> Dict[str, float]:
    # 糖酵解 - 修复震荡问题
    # 1. 计算抑制系数：使用更平缓的响应防止快速切换
    ins = ctx.env.getSignal("insulin")
    glc = ctx.env.getSignal("glucagon")
    
    # 使用更平缓的sigmoid函数 (1.5 而不是 2.0)
    inhibition = 0.8 / (1.0 + np.exp(1.5 * (glc - ins - 0.5))) + 0.2
    
    # 2. 收集所有子反应结果
    res1 = hexokinase_step(ctx)
    res2 = pfk1_step(ctx)
    res3 = pyruvate_kinase_step(ctx)
    res4 = pyruvate_destination_logic(ctx)
    
    # 3. 汇总所有变化，添加平滑因子防止快速震荡
    combined = {}
    for res in [res1, res2, res3, res4]:
        for k, v in res.items():
            combined[k] = combined.get(k, 0.0) + v * inhibition * 0.9  # 添加0.9平滑因子
    
    # 4. 统一写入环境
    ctx.write(combined)
    return combined

def orchestrateLipidMetabolism(ctx: Ctx) -> Dict[str, float]:
    outputs = {}
    for fn in (fattyAcidSynthesis, deNovoLipogenesis, lipidTransport, adiposeLipolysis, betaOxidation):
        res = fn(ctx)
        for k, v in res.items():
            outputs[k] = outputs.get(k, 0.0) + v
    ctx.write(outputs)
    return outputs

def orchestrateAminoAcidMetabolism(ctx: Ctx) -> Dict[str, float]:
    o1 = aminoAcidCatabolism(ctx)
    o2 = aminoAcidSynthesisTransport(ctx)
    outputs = {}
    for o in (o1, o2):
        for k, v in o.items():
            outputs[k] = outputs.get(k, 0.0) + v
    ctx.write(outputs)
    return outputs

def orchestrateEnergyHomeostasis(ctx: Ctx) -> Dict[str, float]:
    outputs = {}
    # 1. 氧化磷酸化是 ATP 的核心来源，必须始终运行
    # 2. 氧气供应是补充氧气的主要来源
    o1 = oxidativePhosphorylation(ctx)
    o2 = oxygen_supply(ctx)
    for o in (o1, o2):
        for k, v in o.items(): outputs[k] = outputs.get(k, 0.0) + v
    # 3. 酮体生成是“备用电源”，仅在血糖低时激活，但不应切断主电源
    glucose = ctx.env.getMetabolite("glucose")
    if glucose < 4.5: # 稍微提高触发阈值，但采用累加逻辑
        keto = ketogenesis(ctx)
        for k, v in keto.items(): outputs[k] = outputs.get(k, 0.0) + v
    ctx.write(outputs)
    return outputs

def orchestrateNADHomeostasis(ctx: Ctx) -> Dict[str, float]:
    outputs = {}
    o1 = lactateFermentation(ctx)
    o2 = nampt_Salvage(ctx)
    o3 = deNovoNADSynthesis(ctx)
    for o in (o1, o2, o3):
        for k, v in o.items():
            outputs[k] = outputs.get(k, 0.0) + v
    ctx.write(outputs)
    return outputs

def cytosolicATPase_load(ctx: Ctx) -> Dict[str, float]:
    atp = ctx.env.getMetabolite("atp")
    # rate = ctx.rate_modifier * min(atp, 50.0) * 0.03
    # 原代码 min(atp, 50.0) 在生理单位下永远等于 atp，导致消耗过快
    rate = ctx.rate_modifier * min(atp, 2.0) * 0.1
    ctx.env.recordRate("cytosolicATPase_load", rate)
    return {"atp": -rate, "adp": rate}

def orchestrateUreaCycle(ctx: Ctx) -> Dict[str, float]:
    o1 = cps1_Ammonia_to_CarbamoylPhosphate(ctx)
    o2 = otc_CarbamoylPhosphate_to_Citrulline(ctx)
    o3 = ass1_Citrulline_to_ASP_Argininosuccinate(ctx)
    o4 = asl_Argininosuccinate_to_Arginine_Fumarate(ctx)
    outputs = {}
    for o in (o1, o2, o3, o4):
        for k, v in o.items():
            outputs[k] = outputs.get(k, 0.0) + v
    ctx.write(outputs)
    return outputs

def orchestrateDetoxification(ctx: Ctx) -> Dict[str, float]:
    o1 = phaseI_OxRed(ctx)
    o2 = phaseII_Conjugation(ctx)
    o3 = ethanol_ADH(ctx)
    o4 = acetaldehyde_ALDH(ctx)
    o5 = acetate_to_acetylcoa(ctx)
    o6 = bilirubinUGT(ctx)
    outputs = {}
    for o in (o1, o2, o3, o4, o5, o6):
        for k, v in o.items():
            outputs[k] = outputs.get(k, 0.0) + v
    ctx.write(outputs)
    return outputs

def orchestrateSynthesisSecretion(ctx: Ctx) -> Dict[str, float]:
    o1 = bileAcidSynthesis(ctx)
    o2 = plasmaProteinSynthesis(ctx)
    o3 = coagulationFactorSynthesis(ctx)
    outputs = {}
    for o in (o1, o2, o3):
        for k, v in o.items():
            outputs[k] = outputs.get(k, 0.0) + v
    ctx.write(outputs)
    return outputs

def signalDegradationModule(ctx: Ctx) -> Dict[str, float]:
    o1 = degradeInsulin(ctx)
    o2 = degradeGlucagon(ctx)
    o3 = inactivateCatecholamines(ctx)
    signals = {}
    for o in (o1, o2, o3):
        for k, v in o.get("signals", {}).items():
            signals[k] = signals.get(k, 0.0) + v
    return {"signals": signals}

def orchestrateSystemSignals(ctx: Ctx) -> Dict[str, float]:
    o1 = hormoneSignalTransduction(ctx)
    o2 = neuralSignalIntegration(ctx)
    o3 = immuneSignalInteraction(ctx)
    o4 = signalDegradationModule(ctx)
    signals = {}
    parameters = {}
    for o in (o1, o2, o3, o4):
        for k, v in o.get("signals", {}).items():
            signals[k] = signals.get(k, 0.0) + v
        for k, v in o.get("parameters", {}).items():
            parameters[k] = parameters.get(k, 0.0) + v
    for s, dv in signals.items():
        cur = ctx.env.getSignal(s)
        ctx.env.setSignal(s, cur + dv)
    for p, dv in parameters.items():
        cur = ctx.env.getParameter(p)
        ctx.env.setParameter(p, cur + dv)
    return {"signals": signals, "parameters": parameters}

def applyEnergyDeficitPolicies(ctx: Ctx) -> None:
    atp = ctx.env.getMetabolite("atp")
    nadh = ctx.env.getMetabolite("nadh")
    nadp = ctx.env.getMetabolite("nad_plus")
    etoh = ctx.env.getMetabolite("ethanol")
    # 生理 ATP 正常在 2-5 之间，低于 1.5 才算危机
    if atp < 1.5: 
        ctx.applyAction("downscale_rates", 0.3)
    else:
        ctx.applyAction("downscale_rates", 1.0)
    # 酒精阈值也要调低
    if etoh > 0.1: 
        ctx.applyAction("downscale_rates", ctx.rate_modifier * 0.8)

def update_hormones(ctx: Ctx) -> Dict[str, Dict[str, float]]:
    glucose = ctx.env.getMetabolite("glucose")
    # --- 胰岛素 (Insulin) ---
    # 使用更平缓的响应曲线，减少震荡
    target_insulin = 0.05 + 0.95 * (glucose / (glucose + 8.0))  # 从5.0增加到8.0，更平缓
    
    # --- 胰高血糖素 (Glucagon) ---
    # 使用更平缓的响应曲线
    target_glucagon = 0.05 + 0.85 * (1.0 / (glucose + 1.0))  # 从0.4/0.9改为1.0/0.85，更平缓

    current_ins = ctx.env.getSignal("insulin")
    current_glc = ctx.env.getSignal("glucagon")
    # 降低响应速度，减少快速震荡
    secretion_ins = max(0, (target_insulin - current_ins) * 0.05)  # 从0.1降低到0.05
    secretion_glc = max(0, (target_glucagon - current_glc) * 0.05)  # 从0.1降低到0.05
    return {"signals": {"insulin": secretion_ins, "glucagon": secretion_glc}}

def hormoneSignalTransduction(ctx: Ctx) -> Dict[str, float]:
    return update_hormones(ctx)

def neuralSignalIntegration(ctx: Ctx) -> Dict[str, float]:
    ep = ctx.env.getSignal("epinephrine")
    new_ep = min(max(ep, 0.05), 2.0)
    return {"signals": {"epinephrine": new_ep - ep}}

def immuneSignalInteraction(ctx: Ctx) -> Dict[str, float]:
    infl = ctx.env.getSignal("inflammation")
    new_infl = max(infl - 0.001, 0.0)
    sens = ctx.env.getParameter("insulin_sensitivity")
    new_sens = max(0.5, 1.0 - 0.5 * new_infl)
    return {"signals": {"inflammation": new_infl - infl}, "parameters": {"insulin_sensitivity": new_sens - sens}}

def degradeInsulin(ctx: Ctx) -> Dict[str, float]:
    ide = ctx.env.getParameter("insulin_degrading_enzyme_activity")
    ins = ctx.env.getSignal("insulin")
    degradation_rate = 0.02 * ide * ins
    new_ins = max(ins - degradation_rate, 0.0)
    return {"signals": {"insulin": new_ins - ins}}

def degradeGlucagon(ctx: Ctx) -> Dict[str, float]:
    gl = ctx.env.getSignal("glucagon")
    new_gl = max(gl - 0.01, 0.0)
    return {"signals": {"glucagon": new_gl - gl}}

def inactivateCatecholamines(ctx: Ctx) -> Dict[str, float]:
    ep = ctx.env.getSignal("epinephrine")
    new_ep = max(ep - 0.01, 0.0)
    return {"signals": {"epinephrine": new_ep - ep}}

class LiverMetabolismSystem:
    def __init__(self, env: MetabolicEnvironment):
        self.env = env
        self.ctx = Ctx(env)

    def step(self, t: int):
        pool = ResourcePool(self.env)
        renv = ResourceEnv(pool)
        rctx = Ctx(renv)
        orchestrateSystemSignals(rctx)
        applyEnergyDeficitPolicies(rctx)
        tasks = [
            orchestrateGlycolysis,
            orchestrateGluconeogenesis,
            g6pase_G6P_to_Glucose,
            orchestrateGlycogen,
            orchestrateEnergyHomeostasis,
            orchestrateNADHomeostasis,
            cytosolicATPase_load,
            orchestrateLipidMetabolism,
            # orchestrateAminoAcidMetabolism,
            # orchestrateUreaCycle,
            # orchestrateSynthesisSecretion,
            orchestrateDetoxification,
        ]
        with ThreadPoolExecutor(max_workers=len(tasks)) as ex:
            futs = [ex.submit(fn, rctx) for fn in tasks]
            for f in futs:
                _ = f.result()
        drained = pool.drain()
        self.env.writeOutputs(drained["metabolites"])
        for s, v in drained["signals"].items():
            self.env.setSignal(s, v)
        self.env.current_rates.update({k: float(v) for k, v in drained.get("rates", {}).items()})
        self.env.update_history(t)
