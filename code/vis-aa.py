import os
from utils import run_metabolic_simulation, generate_dashboard, run_metabolic_tests

AA_CONCENTRATIONS = [
    ("insulin", "Insulin(胰岛素)", "orange", False),
    ("glucagon", "Glucagon(胰高血糖素)", "violet", False),
    ("glucose", "Glucose(葡萄糖)", "royalblue", False),
    ("protein_store", "Protein Store(蛋白储备)", "darkgreen", False),
    ("amino_acid", "Amino Acids(氨基酸)", "teal", False),
    ("pyruvate", "Pyruvate(丙酮酸)", "darkorange", False),
    ('lactate', 'Lactate(乳酸)', 'brown', False),
    ("ammonia", "Ammonia(氨/NH3)", "red", False),
    ("urea", "Urea(尿素)", "green", True),
    ("atp", "ATP", "gold", False),
    ("adp", "ADP", "lightsalmon", False),
    ("nad_plus", "NAD+", "purple", False),
    ("nadh", "NADH", "grey", False),
]

AA_RATES = [
    ("rate_lactate_production", "LDH/丙酮酸去路", "green"),
    ('rate_adiposeLipolysis', '脂质分解', 'darkred'),
    ("rate_protein_metabolism", "蛋白合成/分解净速率", "orange"),
    ("rate_aa_catabolism_step", "氨基酸氧化分解", "royalblue"),
    ("rate_lactate_production", "乳酸生成", "purple"),
    # ("rate_orchestrateGluconeogenesis", "糖异生", "brown"),
    ("rate_urea_cycle", "尿素循环净速率", "red"),
    ("rate_metabolite_export", "尿素排泄/氨基酸吸收", "grey"),
]


def setup_high_protein(env, system, hour, minute):
    if minute % 360 == 0 and minute > 0:
        env.setMetabolite("glucose", env.getMetabolite("glucose") + 5.0)
        env.setMetabolite("amino_acid", env.getMetabolite("amino_acid") + 5.0)


def setup_fasting(env, system, hour, minute):
    pass


def setup_hyperammonemia(env, system, hour, minute):
    if minute in (10, 40, 70):
        env.setMetabolite("ammonia", env.getMetabolite("ammonia") + 0.8)


if __name__ == "__main__":
    hist_high = run_metabolic_simulation(setup_high_protein, hours=18)
    run_metabolic_tests(hist_high, title="高蛋白餐后场景 - 氨基酸代谢约束测试")
    generate_dashboard(
        hist_high,
        "../results/results-html/aa_high_protein.html",
        concentrations=AA_CONCENTRATIONS,
        rates=AA_RATES,
        dashboard_title="肝脏氨基酸代谢模拟 - 高蛋白餐后",
    )

    # hist_fast = run_metabolic_simulation(setup_fasting, hours=10)
    # run_metabolic_tests(hist_fast, title="饥饿/分解代谢场景 - 氨基酸代谢约束测试")
    # generate_dashboard(
    #     hist_fast,
    #     "../results/results-html/aa_fasting.html",
    #     concentrations=AA_CONCENTRATIONS,
    #     rates=AA_RATES,
    #     dashboard_title="肝脏氨基酸代谢模拟 - 饥饿/分解代谢",
    # )

    # hist_hyper = run_metabolic_simulation(setup_hyperammonemia, hours=4)
    # run_metabolic_tests(hist_hyper, title="高氨负荷场景 - 氨基酸代谢与尿素循环测试")
    # generate_dashboard(
    #     hist_hyper,
    #     "../results/results-html/aa_hyperammonemia.html",
    #     concentrations=AA_CONCENTRATIONS,
    #     rates=AA_RATES,
    #     dashboard_title="肝脏氨基酸代谢模拟 - 高氨负荷",
    # )
