import os
from utils import run_metabolic_simulation, generate_dashboard, run_metabolic_tests

# --- 可视化配置 ---
# 格式: (代谢物名, 显示标签, 颜色, 是否使用次坐标轴)
NAFLD_CONCENTRATIONS = [
    ('insulin', 'Insulin(胰岛素)', 'orange', False),
    ('glucagon', 'Glucagon(胰高血糖素)', 'violet', False),
    ('glucose', 'Glucose(葡萄糖)', 'royalblue', False),
    ('fatty_acid', 'Fatty Acid(脂肪酸)', 'cornflowerblue', False),
    ('pyruvate', 'Pyruvate(丙酮酸)', 'cyan', False),
    ('oxygen', 'Oxygen(氧气)', 'teal', False),
    ('acetyl_coa', 'Acetyl-CoA', 'brown', False),
    ('glycerol', 'glycerol(甘油)', 'purple', False),
    ('triglycerides', 'Triglycerides(甘油三酯)', 'green', True),
    ('atp', 'ATP', 'gold', False),
    ('adp', 'ADP', 'lightsalmon', False),
    ('nad_plus', 'NAD+', 'lightgreen', False),
    ('nadh', 'NADH', 'darkgrey', False),
    ('nadph', 'NADPH', 'darkorange', False),
]

# 格式: (反应速率名, 显示标签, 颜色)
NAFLD_RATES = [
    ('rate_hexokinase', '己糖激酶 (HK/GK) 反应', 'blue'),
    ('rate_pfk1', '磷酸果糖激酶-1 (PFK-1) 反应', 'lime'),
    ('rate_pyruvate_kinase', '丙酮酸激酶 (PK) 反应', 'red'),
    ('rate_lactate_production', '乳酸脱氢酶 (LDH) / 丙酮酸去路反应', 'cyan'),
    ('rate_g6pase_G6P_to_Glucose', 'G6P 释放回血糖', 'magenta'),
    ('rate_orchestrateGluconeogenesis', '糖异生', 'purple'),
    ('rate_glycogen_synthesis_total', '糖原合成', 'lightgreen'),
    ('rate_glycogen_breakdown_total', '糖原分解', 'gold'),
    ('rate_fattyAcidSynthesis', '脂肪酸合成', 'orange'),
    ('rate_betaOxidation', 'β-氧化', 'teal'),
    ('rate_deNovoLipogenesis', '新生脂质合成', 'darkorange'),
    ('rate_lipidTransport', '脂质运输', 'navy'),
    ('rate_adiposeLipolysis', '脂质分解', 'darkred'),
    ('rate_lactateFermentation', '乳酸发酵', 'darkgrey'),
    ('rate_oxidativePhosphorylation', '氧化磷酸化', 'lightsalmon'),
]

# --- 模拟逻辑配置 ---

def setup_normal_case(env, system, hour, minute):
    """正常代谢场景配置"""
    if minute == 0:
        print("Initializing Normal Case...")
        env.setSignal("insulin", 0.5)
        env.setSignal("glucagon", 0.5)
        env.setMetabolite("glucose", 5.0)
    
    # 每 6 小时进食一次
    if minute % 360 == 0 and minute > 0:
        env.setMetabolite("glucose", env.getMetabolite("glucose") + 5.0)


if __name__ == "__main__":
    # 1. 运行正常场景模拟
    hist_normal = run_metabolic_simulation(setup_normal_case, hours=18)
    
    # 运行约束测试
    run_metabolic_tests(hist_normal, title="正常场景 - 代谢约束测试")

    generate_dashboard(
        hist_normal, 
        "../results/results-html/lipid_normal.html",
        concentrations=NAFLD_CONCENTRATIONS,
        rates=NAFLD_RATES,
        dashboard_title="肝脏脂质代谢模拟 - 正常场景"
    )
