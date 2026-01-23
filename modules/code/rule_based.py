import pandas as pd
import numpy as np
from typing import Dict, List, Callable, Optional, Tuple

class MetabolicEnvironment:
    def __init__(self):
        # 初始代谢物浓度
        self.metabolites = {
            "glucose": 5.0,          # mmol/L
            "glycogen": 20.0,        # g
            "fatty_acid": 0.5,       # mmol/L
            "triglycerides": 1.0,    # mmol/L
            "cholesterol": 4.5,      # mmol/L
            "amino_acid": 4.0,       # mmol/L
            "ammonia": 0.03,         # mmol/L
            "urea": 5.0,             # mmol/L
            "indirect_bilirubin": 1.0, # μmol/L
            "direct_bilirubin": 0.5, # μmol/L
            "udpga": 2.0,            # mmol/L
            "phaseI_intermediates": 0.1, # mmol/L
            "conjugates": 0.0,       # mmol/L
            "nadh": 0.1,             # mmol/L
            "nad_plus": 0.3,         # mmol/L
            "atp": 5.0,              # mmol/L
            "adp": 1.0,              # mmol/L
            "amp": 0.1,              # mmol/L
            "insulin": 10.0,          # μU/mL
            "glucagon": 5.0,          # pg/mL
            "ketone_body": 0.1,       # mmol/L
            "albumin": 45.0,          # g/L
            "ethanol": 0.0,           # mmol/L
            "acetaldehyde": 0.0,      # mmol/L
            "acetate": 0.0,           # mmol/L
            "paps": 1.0,              # mmol/L
            "gsh": 2.0,               # mmol/L
        }
        
        # 参数
        self.parameters = {
            "is_postprandial": False,
            "insulin_degrading_enzyme_activity": 1.0,
            "liver_function": 1.0,
            "xenobiotic_load": 0.0,
            "rate_modifier": 0.1,     # 反应速率修饰符
            "time_step": 1.0/60.0,    # 时间步长（小时）
        }
        
        # 酶动力学参数
        self.kinetic_parameters = {
            "km_michaelis_menten": {
                "ethanol": 0.5,        # mmol/L
                "glucose": 1.0,        # mmol/L
                "fatty_acid": 0.2,     # mmol/L
                "amino_acid": 2.0,     # mmol/L
                "ammonia": 0.05,       # mmol/L
                "indirect_bilirubin": 1.5, # μmol/L
                "phaseI_intermediates": 0.2, # mmol/L
            },
            "vmax_michaelis_menten": {
                "ethanol": 0.5,        # mmol/L/h
                "glucose": 1.0,        # mmol/L/h
                "fatty_acid": 0.3,     # mmol/L/h
                "amino_acid": 0.8,     # mmol/L/h
                "ammonia": 0.1,        # mmol/L/h
                "indirect_bilirubin": 0.5, # μmol/L/h
                "phaseI_intermediates": 0.4, # mmol/L/h
            },
        }
        
        # 历史记录
        self.history = []
        
    def getMetabolite(self, name: str) -> float:
        return self.metabolites.get(name, 0.0)
    
    def setMetabolite(self, name: str, value: float):
        # 应用边界条件
        bounds = {
            "glucose": (3.0, 10.0),          # mmol/L
            "glycogen": (0.0, 100.0),        # g
            "fatty_acid": (0.1, 2.0),        # mmol/L
            "triglycerides": (0.5, 2.0),     # mmol/L
            "cholesterol": (3.0, 6.0),       # mmol/L
            "amino_acid": (2.0, 8.0),        # mmol/L
            "ammonia": (0.01, 0.1),          # mmol/L
            "urea": (2.5, 7.1),              # mmol/L
            "indirect_bilirubin": (0.1, 20.0), # μmol/L
            "direct_bilirubin": (0.1, 7.0),  # μmol/L
            "udpga": (0.1, 5.0),             # mmol/L
            "phaseI_intermediates": (0.0, 1.0), # mmol/L
            "conjugates": (0.0, 2.0),        # mmol/L
            "nadh": (0.05, 1.0),             # mmol/L
            "nad_plus": (0.1, 1.0),          # mmol/L
            "atp": (2.0, 10.0),              # mmol/L
            "adp": (0.5, 2.0),               # mmol/L
            "amp": (0.05, 0.5),              # mmol/L
            "insulin": (2.0, 50.0),          # μU/mL
            "glucagon": (2.0, 20.0),         # pg/mL
            "ketone_body": (0.05, 5.0),      # mmol/L
            "albumin": (30.0, 55.0),         # g/L
            "ethanol": (0.0, 50.0),          # mmol/L
            "acetaldehyde": (0.0, 5.0),      # mmol/L
            "acetate": (0.0, 10.0),          # mmol/L
            "paps": (0.1, 3.0),              # mmol/L
            "gsh": (0.5, 5.0),               # mmol/L
        }
        
        if name in bounds:
            min_val, max_val = bounds[name]
            value = max(min_val, min(max_val, value))
        else:
            value = max(0.0, value)
        
        self.metabolites[name] = value
    
    def getParameter(self, name: str) -> float:
        return self.parameters.get(name, 0.0)
    
    def setParameter(self, name: str, value: float):
        self.parameters[name] = value
    
    def getKineticParameter(self, param_type: str, substrate: str) -> float:
        return self.kinetic_parameters.get(param_type, {}).get(substrate, 1.0)
    
    def record(self, time: float):
        record = {"time": time}
        record.update(self.metabolites)
        record.update(self.parameters)
        self.history.append(record)
    
    def update_energy_state(self):
        # 更新能量状态（ATP/ADP/AMP平衡）
        atp = self.getMetabolite("atp")
        adp = self.getMetabolite("adp")
        amp = self.getMetabolite("amp")
        
        # 维持总腺苷酸池相对稳定
        total_adenylate = atp + adp + amp
        target_total = 6.1  # ATP + ADP + AMP 初始总和
        
        if total_adenylate != target_total:
            # 调整AMP浓度来维持总腺苷酸池
            delta = target_total - total_adenylate
            new_amp = amp + delta
            self.setMetabolite("amp", new_amp)
    
    def update_oxidation_reduction_state(self):
        # 更新氧化还原状态（NADH/NAD+平衡）
        nadh = self.getMetabolite("nadh")
        nad_plus = self.getMetabolite("nad_plus")
        
        # 维持NADH/NAD+比例在合理范围内
        total_nad = nadh + nad_plus
        target_total = 0.4  # NADH + NAD+ 初始总和
        
        if total_nad != target_total:
            # 调整NAD+浓度来维持总NAD池
            delta = target_total - total_nad
            new_nad_plus = nad_plus + delta
            self.setMetabolite("nad_plus", new_nad_plus)


class RuleBasedLiverSystem:
    def __init__(self, env: MetabolicEnvironment):
        self.env = env
    
    def step(self, time: float):
        # 记录当前状态
        self.env.record(time)
        
        # 执行各种代谢途径（按照时间尺度排序）
        # 快速反应（毫秒-秒级）
        self.process_energy_state()
        self.process_oxidation_reduction_state()
        
        # 中速反应（秒-分钟级）
        self.process_insulin_degradation()
        self.process_ethanol_metabolism()
        self.process_bilirubin_metabolism()
        self.process_phaseII_conjugation()
        self.process_glucose_homeostasis()
        self.process_urea_cycle()
        self.process_lipid_metabolism()
        
        # 慢速反应（分钟-小时级）
        self.process_albumin_synthesis()
    
    def michaelis_menten_rate(self, substrate: str, substrate_concentration: float) -> float:
        # Michaelis-Menten动力学计算反应速率
        km = self.env.getKineticParameter("km_michaelis_menten", substrate)
        vmax = self.env.getKineticParameter("vmax_michaelis_menten", substrate)
        rate = (vmax * substrate_concentration) / (km + substrate_concentration)
        return rate * self.env.getParameter("rate_modifier")
    
    def process_energy_state(self):
        # 处理能量状态（ATP/ADP/AMP平衡）
        self.env.update_energy_state()
    
    def process_oxidation_reduction_state(self):
        # 处理氧化还原状态（NADH/NAD+平衡）
        self.env.update_oxidation_reduction_state()
    
    def process_insulin_degradation(self):
        # 胰岛素降解规则
        ide_activity = self.env.getParameter("insulin_degrading_enzyme_activity")
        insulin = self.env.getMetabolite("insulin")
        
        # 胰岛素降解速率与IDE活性成正比（非线性关系）
        # 调整公式以增加IDE活性对降解速率的影响
        base_degradation_rate = 0.2 * self.env.getParameter("rate_modifier")
        # 使IDE活性的影响更加显著
        ide_effect = ide_activity / (0.5 + ide_activity)
        # 胰岛素浓度的影响
        insulin_effect = insulin / (3.0 + insulin)
        # 综合计算降解速率
        degradation_rate = base_degradation_rate * ide_effect * insulin_effect * (1.0 + ide_activity)
        new_insulin = insulin - degradation_rate
        
        self.env.setMetabolite("insulin", new_insulin)
    
    def process_ethanol_metabolism(self):
        # 乙醇代谢规则
        ethanol = self.env.getMetabolite("ethanol")
        acetaldehyde = self.env.getMetabolite("acetaldehyde")
        acetate = self.env.getMetabolite("acetate")
        nadh = self.env.getMetabolite("nadh")
        nad_plus = self.env.getMetabolite("nad_plus")
        
        if ethanol > 0:
            # 乙醇脱氢酶：乙醇→乙醛（Michaelis-Menten动力学）
            adh_rate = self.michaelis_menten_rate("ethanol", ethanol)
            ethanol_degraded = min(ethanol, adh_rate)
            acetaldehyde_produced = ethanol_degraded
            
            # 乙醛脱氢酶：乙醛→乙酸（Michaelis-Menten动力学，考虑产物抑制）
            # 乙醛脱氢酶活性受NADH/NAD+比例抑制
            redox_ratio = nadh / (nad_plus + 0.01)
            inhibition_factor = 1.0 / (1.0 + 2.0 * redox_ratio)
            aldh_rate = 0.15 * self.env.getParameter("rate_modifier") * inhibition_factor
            acetaldehyde_degraded = min(acetaldehyde + acetaldehyde_produced, aldh_rate)
            acetate_produced = acetaldehyde_degraded
            
            # NADH产生
            nadh_produced = ethanol_degraded + acetaldehyde_degraded
            nad_plus_consumed = nadh_produced
            
            # 更新代谢物
            self.env.setMetabolite("ethanol", ethanol - ethanol_degraded)
            self.env.setMetabolite("acetaldehyde", acetaldehyde + acetaldehyde_produced - acetaldehyde_degraded)
            self.env.setMetabolite("acetate", acetate + acetate_produced)
            self.env.setMetabolite("nadh", nadh + nadh_produced)
            self.env.setMetabolite("nad_plus", nad_plus - nad_plus_consumed)
    
    def process_bilirubin_metabolism(self):
        # 胆红素代谢规则
        indirect_bilirubin = self.env.getMetabolite("indirect_bilirubin")
        direct_bilirubin = self.env.getMetabolite("direct_bilirubin")
        udpga = self.env.getMetabolite("udpga")
        
        if indirect_bilirubin > 0 and udpga > 0:
            # 葡萄糖醛酸转移酶：间接胆红素→直接胆红素（Michaelis-Menten动力学）
            conjugation_rate = self.michaelis_menten_rate("indirect_bilirubin", indirect_bilirubin) * self.env.getParameter("liver_function")
            # 考虑UDPGA浓度对反应的影响
            udpga_effect = udpga / (1.0 + udpga)
            conjugation_rate *= udpga_effect
            
            bilirubin_conjugated = min(indirect_bilirubin, conjugation_rate)
            udpga_consumed = bilirubin_conjugated * 1.0  # 1:1 化学计量比
            
            # 更新代谢物
            self.env.setMetabolite("indirect_bilirubin", indirect_bilirubin - bilirubin_conjugated)
            self.env.setMetabolite("direct_bilirubin", direct_bilirubin + bilirubin_conjugated)
            self.env.setMetabolite("udpga", udpga - udpga_consumed)
    
    def process_phaseII_conjugation(self):
        # 相II结合规则
        phaseI_intermediates = self.env.getMetabolite("phaseI_intermediates")
        conjugates = self.env.getMetabolite("conjugates")
        udpga = self.env.getMetabolite("udpga")
        paps = self.env.getMetabolite("paps")
        gsh = self.env.getMetabolite("gsh")
        
        if phaseI_intermediates > 0:
            # 相II结合反应（Michaelis-Menten动力学）
            conjugation_rate = self.michaelis_menten_rate("phaseI_intermediates", phaseI_intermediates) * self.env.getParameter("liver_function")
            intermediates_conjugated = min(phaseI_intermediates, conjugation_rate)
            
            # 消耗辅因子（根据辅因子可用性分配）
            total_cofactor = udpga + paps + gsh
            if total_cofactor > 0:
                udpga_fraction = udpga / total_cofactor
                paps_fraction = paps / total_cofactor
                gsh_fraction = gsh / total_cofactor
                
                udpga_consumed = intermediates_conjugated * udpga_fraction
                paps_consumed = intermediates_conjugated * paps_fraction
                gsh_consumed = intermediates_conjugated * gsh_fraction
                
                # 更新代谢物
                self.env.setMetabolite("phaseI_intermediates", phaseI_intermediates - intermediates_conjugated)
                self.env.setMetabolite("conjugates", conjugates + intermediates_conjugated)
                self.env.setMetabolite("udpga", udpga - udpga_consumed)
                self.env.setMetabolite("paps", paps - paps_consumed)
                self.env.setMetabolite("gsh", gsh - gsh_consumed)
    
    def process_glucose_homeostasis(self):
        # 糖代谢规则
        glucose = self.env.getMetabolite("glucose")
        glycogen = self.env.getMetabolite("glycogen")
        insulin = self.env.getMetabolite("insulin")
        glucagon = self.env.getMetabolite("glucagon")
        is_postprandial = self.env.getParameter("is_postprandial")
        
        # 胰岛素和胰高血糖素对糖代谢的影响（非线性关系）
        insulin_effect = 1.0 + (insulin / 10.0) ** 2
        glucagon_effect = 1.0 + (glucagon / 5.0) ** 2
        
        # 血糖峰值控制
        glucose_initial = 5.0  # 初始血糖值
        glucose_peak_limit = glucose_initial * 2.0
        if glucose > glucose_peak_limit:
            # 血糖超过峰值限制，直接降低血糖
            excess_glucose = glucose - glucose_peak_limit
            self.env.setMetabolite("glucose", glucose_peak_limit)
            # 将多余的血糖转化为糖原
            glycogen_synthesis_rate = excess_glucose * 0.5 * insulin_effect
            new_glycogen = glycogen + glycogen_synthesis_rate
            
            # 糖原储备上限
            if new_glycogen > 100.0:
                # 超过糖原储备上限，多余的糖转化为脂肪
                excess_glycogen = new_glycogen - 100.0
                new_glycogen = 100.0
                self.env.setMetabolite("triglycerides", self.env.getMetabolite("triglycerides") + excess_glycogen * 0.01)
            
            self.env.setMetabolite("glycogen", new_glycogen)
        elif is_postprandial or glucose > 5.5:
            # 餐后或血糖高时：促进糖原合成，抑制糖异生
            glycogen_synthesis_rate = 0.5 * insulin_effect * self.env.getParameter("rate_modifier")
            new_glycogen = glycogen + glycogen_synthesis_rate
            
            # 糖原储备上限
            if new_glycogen > 100.0:
                # 超过糖原储备上限，多余的糖转化为脂肪
                excess_glycogen = new_glycogen - 100.0
                new_glycogen = 100.0
                self.env.setMetabolite("triglycerides", self.env.getMetabolite("triglycerides") + excess_glycogen * 0.01)
            
            self.env.setMetabolite("glycogen", new_glycogen)
            
        elif glucose < 4.0:
            # 血糖低时：促进糖原分解
            glycogenolysis_rate = 0.3 * glucagon_effect * self.env.getParameter("rate_modifier")
            glycogen_degraded = min(glycogen, glycogenolysis_rate)
            glucose_produced = glycogen_degraded * 0.1
            
            self.env.setMetabolite("glycogen", glycogen - glycogen_degraded)
            self.env.setMetabolite("glucose", glucose + glucose_produced)
        
        # 糖酵解（Michaelis-Menten动力学）
        glycolysis_rate = self.michaelis_menten_rate("glucose", glucose)
        glucose_used = min(glucose, glycolysis_rate)
        self.env.setMetabolite("glucose", glucose - glucose_used)
        # 糖酵解产生ATP
        atp_produced = glucose_used * 2
        self.env.setMetabolite("atp", self.env.getMetabolite("atp") + atp_produced)
        # 相应地消耗ADP
        adp_used = atp_produced
        self.env.setMetabolite("adp", self.env.getMetabolite("adp") - adp_used)
        
        # 酮体生成
        if glucose < 4.5 and glycogen < 10.0:
            # 血糖低且糖原储备不足时，生成酮体
            ketogenesis_rate = 0.1 * self.env.getParameter("rate_modifier")
            fatty_acid = self.env.getMetabolite("fatty_acid")
            fatty_acid_used = min(fatty_acid, ketogenesis_rate)
            ketone_produced = fatty_acid_used * 0.5
            
            self.env.setMetabolite("fatty_acid", fatty_acid - fatty_acid_used)
            self.env.setMetabolite("ketone_body", self.env.getMetabolite("ketone_body") + ketone_produced)
    
    def process_urea_cycle(self):
        # 尿素循环规则
        ammonia = self.env.getMetabolite("ammonia")
        urea = self.env.getMetabolite("urea")
        atp = self.env.getMetabolite("atp")
        
        if ammonia > 0.03:
            # 氨解毒：氨→尿素（Michaelis-Menten动力学）
            urea_synthesis_rate = self.michaelis_menten_rate("ammonia", ammonia) * self.env.getParameter("liver_function")
            # 考虑ATP对尿素循环的影响
            atp_effect = atp / (2.0 + atp)
            urea_synthesis_rate *= atp_effect
            
            ammonia_used = min(ammonia, urea_synthesis_rate)
            urea_produced = ammonia_used * 0.5  # 2:1 化学计量比
            atp_used = ammonia_used * 2  # 每分子氨消耗2分子ATP
            
            # 更新代谢物
            self.env.setMetabolite("ammonia", ammonia - ammonia_used)
            self.env.setMetabolite("urea", urea + urea_produced)
            self.env.setMetabolite("atp", atp - atp_used)
            self.env.setMetabolite("adp", self.env.getMetabolite("adp") + atp_used)
    
    def process_albumin_synthesis(self):
        # 白蛋白合成规则
        albumin = self.env.getMetabolite("albumin")
        amino_acid = self.env.getMetabolite("amino_acid")
        atp = self.env.getMetabolite("atp")
        
        # 肝脏每天合成约12g-15g白蛋白，转换为每小时合成率
        # 白蛋白合成速率受氨基酸和ATP浓度的影响（非线性关系）
        base_synthesis_rate = (12.0 / 24.0) * 0.01 * self.env.getParameter("rate_modifier") * self.env.getParameter("liver_function")
        amino_acid_effect = amino_acid / (3.0 + amino_acid)
        atp_effect = atp / (3.0 + atp)
        albumin_synthesis_rate = base_synthesis_rate * amino_acid_effect * atp_effect
        
        if amino_acid > 2.0 and atp > 2.0:
            # 合成白蛋白需要氨基酸和ATP
            amino_acid_used = albumin_synthesis_rate * 0.1
            atp_used = albumin_synthesis_rate * 5.0  # 蛋白质合成需要大量ATP
            
            if amino_acid >= amino_acid_used and atp >= atp_used:
                new_albumin = albumin + albumin_synthesis_rate
                
                # 白蛋白浓度应维持在35-55 g/L
                if new_albumin > 55.0:
                    new_albumin = 55.0
                elif new_albumin < 35.0:
                    # 白蛋白合成率为0或负数，判定为肝衰竭模式
                    pass
                
                self.env.setMetabolite("albumin", new_albumin)
                self.env.setMetabolite("amino_acid", amino_acid - amino_acid_used)
                self.env.setMetabolite("atp", atp - atp_used)
                self.env.setMetabolite("adp", self.env.getMetabolite("adp") + atp_used)
    
    def process_lipid_metabolism(self):
        # 脂代谢规则
        fatty_acid = self.env.getMetabolite("fatty_acid")
        triglycerides = self.env.getMetabolite("triglycerides")
        insulin = self.env.getMetabolite("insulin")
        glucose = self.env.getMetabolite("glucose")
        is_postprandial = self.env.getParameter("is_postprandial")
        
        if is_postprandial:
            # 餐后：促进甘油三酯合成
            # 甘油三酯合成速率受胰岛素和葡萄糖浓度的影响（非线性关系）
            insulin_effect = insulin / (10.0 + insulin)
            glucose_effect = glucose / (5.0 + glucose)
            tg_synthesis_rate = 0.1 * insulin_effect * glucose_effect * self.env.getParameter("rate_modifier")
            
            fatty_acid_used = min(fatty_acid, tg_synthesis_rate)
            new_triglycerides = triglycerides + fatty_acid_used * 0.3
            
            # 肝脏不长期储存脂肪，多余的甘油三酯输出
            if new_triglycerides > 1.8:
                excess_tg = new_triglycerides - 1.8
                new_triglycerides = 1.8
            
            self.env.setMetabolite("fatty_acid", fatty_acid - fatty_acid_used)
            self.env.setMetabolite("triglycerides", new_triglycerides)
        else:
            # 空腹：促进脂肪酸β氧化
            # 脂肪酸β氧化速率受脂肪酸浓度的影响（Michaelis-Menten动力学）
            beta_oxidation_rate = self.michaelis_menten_rate("fatty_acid", fatty_acid)
            fatty_acid_used = min(fatty_acid, beta_oxidation_rate)
            atp_produced = fatty_acid_used * 10
            
            self.env.setMetabolite("fatty_acid", fatty_acid - fatty_acid_used)
            self.env.setMetabolite("atp", self.env.getMetabolite("atp") + atp_produced)
            self.env.setMetabolite("adp", self.env.getMetabolite("adp") - atp_produced)
    
    def process_energy_state(self):
        # 处理能量状态（ATP/ADP/AMP平衡）
        self.env.update_energy_state()
    
    def process_oxidation_reduction_state(self):
        # 处理氧化还原状态（NADH/NAD+平衡）
        self.env.update_oxidation_reduction_state()


def run_simulation(env: MetabolicEnvironment, minutes: int, inject: Optional[Callable] = None) -> pd.DataFrame:
    system = RuleBasedLiverSystem(env)
    for t in range(minutes):
        hour = t / 60.0
        if inject:
            inject(env, t)
        system.step(hour)
    
    df = pd.DataFrame(env.history)
    df["time"] = df["time"]
    return df
