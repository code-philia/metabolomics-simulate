import os
from utils import run_metabolic_simulation, generate_dashboard, run_metabolic_tests

AA_CONCENTRATIONS = [
    ('atp', 'ATP', 'gold', False),
    ('adp', 'ADP', 'lightsalmon', False),
    ('nad_plus', 'NAD+', 'lightgreen', False),
    ('nadh', 'NADH', 'darkgrey', False),
    ('nadp_plus', 'NADP+', 'peru', False),
    ('nadph', 'NADPH', 'darkorange', False),

    ('insulin', 'Insulin(胰岛素)', 'orange', False),
    ('glucagon', 'Glucagon(胰高血糖素)', 'violet', False),

    ('glucose', 'Glucose(葡萄糖)', 'royalblue', False),
    ('g6p', 'G6P(葡萄糖-6-磷酸)', 'lightpink', False),
    ('pyruvate', 'Pyruvate(丙酮酸)', 'cyan', False),
    ('oxygen', 'Oxygen(氧气)', 'blue', False),
    ('acetyl_coa', 'Acetyl-CoA', 'brown', False),

    ('fatty_acid', 'Fatty Acid(脂肪酸)', 'cornflowerblue', False),
    ('glycerol', 'glycerol(甘油)', 'purple', False),
    ('triglycerides', 'Triglycerides(甘油三酯)', 'green', False),
    
    ("protein_store", "Protein Store(蛋白储备)", "darkgreen", False),
    ("amino_acid", "Amino Acids(氨基酸)", "teal", False),
    ('lactate', 'Lactate(乳酸)', 'magenta', False),
    ("ammonia", "Ammonia(氨/NH3)", "red", False),

    ("bile_acid", "Bile Acid(胆汁酸)", "chartreuse", False),
    ("albumin", "Albumin(白蛋白)", "navy", False),
    ("clotting_factor", "凝血因子(Clotting Factor)", "lightblue", False),

    ('ethanol', 'Ethanol(乙醇)', 'darkred', False),
    ('acetaldehyde', 'Acetaldehyde(乙醛)', 'yellow', False),
    ('acetate', 'Acetate(乙酸)', 'pink', False),
]

AA_RATES = [
    ('rate_hexokinase', '己糖激酶 (HK/GK) 反应', 'blue'),
    ('rate_pfk1', '磷酸果糖激酶-1 (PFK-1) 反应', 'lime'),
    ('rate_pyruvate_kinase', '丙酮酸激酶 (PK) 反应', 'red'),
    ('rate_lactate_production', '乳酸脱氢酶 (LDH) / 丙酮酸去路反应', 'cyan'),

    ('rate_pentosePhosphatePathway', '磷酸戊糖途径', 'peru'),
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
    ('rate_tca_cycle', 'TCA 循环', 'darkblue'),
    ('rate_oxidativePhosphorylation', '氧化磷酸化', 'lightsalmon'),

    ("rate_protein_metabolism", "蛋白合成/分解净速率", "violet"),
    ("rate_aa_catabolism_step", "氨基酸氧化分解", "royalblue"),

    ("rate_urea_cycle", "尿素循环净速率", "yellow"),
    ("rate_metabolite_export", "尿素排泄/氨基酸吸收", "grey"),

    ("rate_bileAcidSynthesis", "胆汁酸合成", "chartreuse"),
    ("rate_bileExcretion", "胆汁酸排泄", "pink"),
    ("rate_plasmaProteinSynthesis", "血浆蛋白合成", "darkgreen"),
    ("rate_coagulationFactorSynthesis", "凝血因子合成", "lightblue"),

    ('rate_ethanol_ADH', '乙醇脱氢酶 (ADH) 速率', 'lightcoral'),
    ('rate_acetaldehyde_ALDH', '乙醛脱氢酶 (ALDH) 速率', 'brown'),
    ('rate_acetate_to_acetylcoa', '乙酸→乙酰辅酶A 速率', 'cornflowerblue'),
]


def setup_normal(env, system, hour, minute):
    if minute % 360 == 0 and minute > 0:
        env.setMetabolite("glucose", env.getMetabolite("glucose") + 5.0)
        env.setMetabolite("triglycerides", env.getMetabolite("triglycerides") + 5.0)
        env.setMetabolite("amino_acid", env.getMetabolite("amino_acid") + 5.0)
    if minute == 360 * 2:
        env.setMetabolite("ethanol", env.getMetabolite("ethanol") + 0.5)



if __name__ == "__main__":
    hist_normal = run_metabolic_simulation(setup_normal, hours=15)
    run_metabolic_tests(hist_normal, title="正常餐后场景 - 代谢约束测试")
    generate_dashboard(
        hist_normal,
        "../results/results-html/all_normal.html",
        concentrations=AA_CONCENTRATIONS,
        rates=AA_RATES,
        dashboard_title="肝脏代谢模拟 - 正常餐后",
    )