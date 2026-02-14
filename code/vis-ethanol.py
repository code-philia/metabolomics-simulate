import os
from utils import run_metabolic_simulation, generate_dashboard

# --- 可视化配置 ---
# 格式: (代谢物名, 显示标签, 颜色, 是否使用次坐标轴)
ALCOHOL_CONCENTRATIONS = [
    ('ethanol', 'Ethanol(乙醇)', 'orange', False),
    ('acetaldehyde', 'Acetaldehyde(乙醛)', 'red', False),
    ('acetate', 'Acetate(乙酸)', 'brown', False),
    ('acetyl_coa', 'Acetyl-CoA', 'green', False),
    ('nadh', 'NADH', 'purple', False),
    ('nad_plus', 'NAD+', 'pink', False),
]

# 格式: (反应速率名, 显示标签, 颜色)
ALCOHOL_RATES = [
    ('rate_ethanol_ADH', '乙醇脱氢酶 (ADH) 速率', 'orange'),
    ('rate_acetaldehyde_ALDH', '乙醛脱氢酶 (ALDH) 速率', 'red'),
    ('rate_acetate_to_acetylcoa', '乙酸→乙酰辅酶A 速率', 'brown'),
]

# --- 模拟逻辑配置 ---

def setup_alcohol_normal_case(env, system, hour, minute):
    """正常乙醇代谢场景配置"""
    # 模拟持续吸收 (10-15分钟)
    if 10 <= minute <= 15:
        env.setMetabolite("ethanol", env.getMetabolite("ethanol") + 0.5)

def setup_alcohol_low_aldh_case(env, system, hour, minute):
    """低 ALDH 活性（乙醛蓄积）场景配置"""
    if minute == 0:
        # 设置 ALDH 活性为极低 (10%)
        # 模拟 ALDH 缺乏（亚洲脸红反应 / 乙醛中毒蓄积）
        env.setParameter("aldh_activity", 0.1)
        
    # 模拟持续吸收 (10-15分钟)
    if 10 <= minute <= 15:
        env.setMetabolite("ethanol", env.getMetabolite("ethanol") + 0.5)

if __name__ == "__main__":
    # 1. 运行正常场景模拟
    print("Running Normal Alcohol Metabolism Simulation...")
    hist_normal = run_metabolic_simulation(setup_alcohol_normal_case, hours=8)
    generate_dashboard(
        hist_normal, 
        "../results/results-html/alcohol_normal.html",
        concentrations=ALCOHOL_CONCENTRATIONS,
        rates=ALCOHOL_RATES,
        dashboard_title="肝脏代谢模拟 - 正常乙醇代谢"
    )
    
    # 2. 运行低 ALDH 活性场景模拟
    print("\nRunning Low ALDH Activity Simulation...")
    hist_low_aldh = run_metabolic_simulation(setup_alcohol_low_aldh_case, hours=8)
    generate_dashboard(
        hist_low_aldh, 
        "../results/results-html/alcohol_low_aldh.html",
        concentrations=ALCOHOL_CONCENTRATIONS,
        rates=ALCOHOL_RATES,
        dashboard_title="肝脏代谢模拟 - 低 ALDH 活性（乙醛蓄积）"
    )
