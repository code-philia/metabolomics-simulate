import os
from utils import run_metabolic_simulation, generate_dashboard, run_metabolic_tests

# --- 可视化配置 ---
# 格式: (代谢物名, 显示标签, 颜色, 是否使用次坐标轴)
GLUCOSE_CONCENTRATIONS = [
    ('insulin', 'Insulin(胰岛素)', 'orange', False),
    ('glucagon', 'Glucagon(胰高血糖素)', 'violet', False),
    ('glucose', 'Glucose(葡萄糖)', 'royalblue', False),
    ('g6p', 'G6P', 'cornflowerblue', False),
    ('f16bp', 'f16bp(中间体)', 'green', True),
    ('pyruvate', 'Pyruvate(丙酮酸)', 'cyan', False),
    ('lactate', 'Lactate(乳酸)', 'teal', False),
    ('acetyl_coa', 'Acetyl-CoA', 'brown', False),
    ('oxygen', 'Oxygen(氧气)', 'navy', False),
    ('atp', 'ATP', 'gold', False),
    ('adp', 'ADP', 'lightsalmon', False),
    ('nad_plus', 'NAD+', 'lightgreen', False),
    ('nadh', 'NADH', 'darkgrey', False),
    ('glycerol', 'glycerol(甘油)', 'purple', False),
    ('amino_acid', 'amino_acid(氨基酸)', 'darkorange', False),
]

# 格式: (反应速率名, 显示标签, 颜色)
GLUCOSE_RATES = [
    ('rate_hexokinase', '己糖激酶 (HK/GK) 反应', 'blue'),
    ('rate_pfk1', '磷酸果糖激酶-1 (PFK-1) 反应', 'lime'),
    ('rate_pyruvate_kinase', '丙酮酸激酶 (PK) 反应', 'red'),
    ('rate_lactate_production', '乳酸脱氢酶 (LDH) / 丙酮酸去路反应', 'cyan'),
    ('rate_g6pase_G6P_to_Glucose', 'G6P 释放回血糖', 'magenta'),
    ('rate_orchestrateGluconeogenesis', '糖异生', 'purple'),
    ('rate_glycogen_synthesis_total', '糖原合成', 'lightgreen'),
    ('rate_glycogen_breakdown_total', '糖原分解', 'gold'),
    ('rate_lactateFermentation', '乳酸发酵', 'darkorange'),
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

def setup_nafld_case(env, system, hour, minute):
    """NAFLD 代谢场景配置"""
    if minute == 0:
        print("Initializing NAFLD Case...")
        env.setSignal("insulin", 0.5)
        env.setSignal("glucagon", 0.5)
        env.setMetabolite("glucose", 5.0)
    
    # 这里可以添加 NAFLD 特有的进食逻辑或参数调整
    # 目前保持与原本 logic 一致（原本代码中 nafld 分支在循环中是 pass）
    pass

if __name__ == "__main__":
    # 1. 运行正常场景模拟
    hist_normal = run_metabolic_simulation(setup_normal_case, hours=15)
    
    # 运行约束测试
    run_metabolic_tests(hist_normal, title="正常场景 - 代谢约束测试")

    generate_dashboard(
        hist_normal, 
        "../results/results-html/glucose_normal.html",
        concentrations=GLUCOSE_CONCENTRATIONS,
        rates=GLUCOSE_RATES,
        dashboard_title="肝脏代谢模拟 - 正常场景"
    )
    
    # 2. 运行 NAFLD 场景模拟
    # hist_nafld = run_metabolic_simulation(setup_nafld_case, hours=24)
    # run_metabolic_tests(hist_nafld, title="NAFLD 场景 - 代谢约束测试")
    # generate_dashboard(
    #     hist_nafld, 
    #     "../results/results-html/glucose_abnormal.html",
    #     concentrations=GLUCOSE_CONCENTRATIONS,
    #     rates=GLUCOSE_RATES,
    #     dashboard_title="肝脏代谢模拟 - 异常场景"
    # )
