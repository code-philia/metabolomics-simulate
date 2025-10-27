import math, random, statistics
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Tuple
import pandas as pd
import matplotlib.pyplot as plt

# --------------------- Reaction and Simulator classes ---------------------
@dataclass
class Reaction:
    name: str
    inputs: Dict[str, float]    # stoichiometric consumption per firing
    outputs: Dict[str, float]   # stoichiometric production per firing
    capacity: float = 1.0       # max firings per timestep (can be fractional)
    threshold: Optional[Tuple[str, float]] = None  # (metabolite, min_conc)
    reversible: bool = False

    def can_fire(self, pool: Dict[str, float]) -> float:
        """Return max number of times this reaction could fire given pool and capacity."""
        # check threshold (e.g., enzyme available)
        if self.threshold:
            met, amt = self.threshold
            if pool.get(met, 0.0) < amt:
                return 0.0
        # determine limiting substrate
        if not self.inputs:
            # pure producer (e.g., uptake)
            return self.capacity
        max_fires = float('inf')
        for m, need in self.inputs.items():
            avail = pool.get(m, 0.0)
            if need <= 0:
                continue
            max_fires = min(max_fires, avail / need)
        if max_fires == float('inf'):
            max_fires = 0.0
        # cannot exceed capacity
        return min(max_fires, self.capacity)

    def fire(self, pool: Dict[str, float], times: float) -> None:
        """Execute reaction times times (consume inputs, produce outputs)."""
        if times <= 0:
            return
        # consume
        for m, need in self.inputs.items():
            pool[m] = pool.get(m, 0.0) - need * times
            # prevent tiny negative due to numerical issues
            if pool[m] < 0 and pool[m] > -1e-9:
                pool[m] = 0.0
        # produce
        for m, prod in self.outputs.items():
            pool[m] = pool.get(m, 0.0) + prod * times


@dataclass
class CellSimulator:
    pool: Dict[str, float]                     # metabolite concentrations (arbitrary units)
    reactions: List[Reaction]                  # all reactions that "compete" each timestep
    dt: float = 1.0                            # timestep scaling (affects uptake/export capacities)
    history: List[Dict[str, float]] = field(default_factory=list)

    def step(self):
        """Perform one producer-consumer style timestep.
        Try to run each reaction once in random order; allow fractional firing up to capacity.
        """
        # random order to avoid ordering bias
        order = list(range(len(self.reactions)))
        random.shuffle(order)
        # snapshot before step for measuring change
        before = self.pool.copy()
        for i in order:
            r = self.reactions[i]
            # compute how many times it can fire
            max_possible = r.can_fire(self.pool)
            if max_possible <= 0:
                continue
            # In biological systems, reaction firing often depends on substrate conc linearly or via Michaelis-Menten.
            # For simplicity, we take a fraction of max_possible proportional to substrate availability and capacity.
            # Here allow full max_possible (greedy) but limited by capacity already.
            fires = max_possible
            # small stochasticity to mimic fluctuating enzyme activity
            fires *= random.uniform(0.9, 1.0)
            r.fire(self.pool, fires)
        # after step, clip negatives
        for k, v in list(self.pool.items()):
            if v < 0:
                self.pool[k] = 0.0
        # record history
        self.history.append(self.pool.copy())
        # return max absolute change
        max_change = max(abs(self.pool.get(k,0.0) - before.get(k,0.0)) for k in set(self.pool) | set(before))
        return max_change

    def run_until_stable(self, tol=1e-4, max_steps=10000, check_window=50):
        """Run until max change < tol for a sliding window of steps (stable), or until max_steps reached."""
        recent_changes = []
        for step in range(max_steps):
            change = self.step()
            recent_changes.append(change)
            if len(recent_changes) > check_window:
                recent_changes.pop(0)
            # check if windowed average change is below tol
            if len(recent_changes) == check_window and statistics.mean(recent_changes) < tol:
                return step+1, True
        return max_steps, False




if __name__ == "__main__":
    # initial_pool = {
    #     "Glc": 10.0,   # internal glucose
    #     "O2": 5.0,    # internal oxygen
    #     "ATP": 2.0,
    #     "ADP": 5.0,
    #     "CO2": 0.1,
    #     "Pi": 5.0,
    #     "NADH": 0.5,
    #     "NAD+": 2.0,
    #     "H2O": 10.0
    # }

    initial_pool = {
        "Glc": 5.0, "O2": 5.0,
        "Pyruvate": 0.5, "AcetylCoA": 0.2, "CoA": 0.2,
        "ATP": 2.0, "ADP": 5.0, "Pi": 5.0, "GDP": 5.0,
        "NADH": 5.0, "NAD+": 5.0,
        "FADH2": 1.0, "FAD": 1.0,
        "CO2": 0.1, "H2O": 10.0,
    }

    # Environment concentrations (available for uptake)
    # external = {
    #     "Glc_ext": 400.0,
    #     "O2_ext": 999.0
    # }
    # external = {
    #     "Glc_ext": 20.0,
    #     "O2_ext": 10.0
    # }

    # reactions = [
    #     # Uptake: environment -> internal (producer)
    #     Reaction("Glc_uptake", inputs={"Glc_ext": 0.5}, outputs={"Glc": 0.5}, capacity=0.524),
    #     Reaction("O2_uptake", inputs={"O2_ext": 0.5}, outputs={"O2": 0.5}, capacity=0.238),
    #     # Reaction("Glc_uptake", inputs={"Glc_ext": 0.5}, outputs={"Glc": 0.5}, capacity=1.0),
    #     # Reaction("O2_uptake", inputs={"O2_ext": 0.5}, outputs={"O2": 0.5}, capacity=1.0),

    #     # Glycolysis: Glc + 2 ADP + 2 Pi -> 2 ATP + 2 NADH + 2 Pyruvate (pyruvate omitted, use CO2 eventually)
    #     Reaction("Glycolysis", inputs={"Glc": 1.0, "ADP": 2.0, "Pi": 2.0, "NAD+": 2.0}, outputs={"ATP": 2.0, "NADH": 2.0, "CO2": 0.4}, capacity=0.5),
        
    #     # Pyruvate oxidation + TCA + OxPhos combined (very coarse): Pyruvate + O2 + ADP + Pi + NADH -> many ATP + CO2 + NAD+
    #     # We combine NADH usage into OxPhos: use 4 NADH -> 12 ATP (coarse)
    #     Reaction("OxidativePhosphorylation", inputs={"NADH": 4.0, "O2": 1.0, "ADP": 4.0, "Pi":4.0}, outputs={"ATP":12.0, "CO2":2.0, "NAD+":4.0, "H2O":2.0}, capacity=0.3, threshold=("NADH", 0.1)),
        
    #     # ATP consumption (cellular work): ATP -> ADP + Pi
    #     Reaction("ATP_use", inputs={"ATP": 0.2}, outputs={"ADP": 0.2, "Pi":0.2}, capacity=5.0),
        
    #     # NAD+ regeneration via side pathways (small)
    #     Reaction("NAD_regen", inputs={"NADH": 0.1}, outputs={"NAD+": 0.1}, capacity=0.5),

    #     # CO2 export (simple sink)
    #     Reaction("CO2_export", inputs={"CO2": 1.0}, outputs={}, capacity=0.5),
    # ]

    reactions = [
        # 1. 糖酵解（输入葡萄糖，产生丙酮酸 + ATP + NADH）
        Reaction("glycolysis", {"Glc": 1, "NAD+": 2, "ADP": 2},
                 {"Pyruvate": 2, "ATP": 2, "NADH": 2}, capacity=0.5),

        # 2. 丙酮酸脱羧生成乙酰辅酶A（连接糖解与TCA）
        Reaction("pyruvate_to_acetylcoa", {"Pyruvate": 1, "CoA": 1, "NAD+": 1},
                 {"AcetylCoA": 1, "CO2": 1, "NADH": 1}, capacity=0.3),

        # 3. 三羧酸循环（产生 NADH、FADH2、GTP）
        Reaction("tca_cycle", {"AcetylCoA": 1, "NAD+": 3, "FAD": 1, "GDP": 1, "Pi": 1, "H2O": 2},
                 {"CO2": 2, "NADH": 3, "FADH2": 1, "GTP": 1, "CoA": 1, "H+": 4}, capacity=0.4),

        # 4. 电子传递链与氧化磷酸化
        Reaction("respiration", {"NADH": 3, "FADH2": 1, "ADP": 4, "Pi": 4, "O2": 1.5},
                 {"ATP": 4, "NAD+": 3, "FAD": 1, "H2O": 3}, capacity=0.4),

        # 5. 维持输入输出（营养和废物交换）
        Reaction("Glc_input", {}, {"Glc": 1}, capacity=0.04),
        Reaction("O2_input", {}, {"O2": 1}, capacity=0.007),
        Reaction("GDP_input", {}, {"GDP": 1}, capacity=0.005),
        Reaction("waste_output", {"CO2": 1, "H2O": 1}, {}, capacity=0.5),

        # ATP消耗
        Reaction("ATP_use", inputs={"ATP": 1}, outputs={"ADP": 1, "Pi":1}, capacity=0.1),

        # NADH穿梭系统
        Reaction("NADH_shuttle", {"NADH": 1}, {"NAD+": 1}, capacity=1)

    ]

    # Include external metabolites in pool so reactions can consume them
    pool = initial_pool.copy()
    # pool.update({"Glc_ext": external["Glc_ext"], "O2_ext": external["O2_ext"]})

    sim = CellSimulator(pool=pool, reactions=reactions)

    # Run simulation
    steps, stable = sim.run_until_stable(tol=1e-3, max_steps=500, check_window=40)

    print(f"Simulation finished after {steps} steps. Stable: {stable}")
    final = sim.history[-1]
    df = pd.DataFrame(sim.history)

    # Plot time series for key metabolites
    plt.figure(figsize=(8,4))
    plt.plot(df.index, df["ATP"], label="ATP")
    plt.xlabel("Timestep")
    plt.ylabel("ATP (a.u.)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'ATP_history.png')

    plt.figure(figsize=(8,4))
    plt.plot(df.index, df["Glc"], label="Glc")
    plt.plot(df.index, df["O2"], label="O2")
    plt.plot(df.index, df["CO2"], label="CO2")
    plt.plot(df.index, df["H2O"], label="H2O")
    plt.plot(df.index, df["ADP"], label="ADP")
    # plt.plot(df.index, df["Pi"], label="Pi")
    plt.plot(df.index, df["NADH"], label="NADH")
    plt.plot(df.index, df["NAD+"], label="NAD+")
    plt.plot(df.index, df["FAD"], label="FAD")
    plt.plot(df.index, df["FADH2"], label="FADH2")
    plt.plot(df.index, df["GDP"], label="GDP")
    plt.plot(df.index, df["AcetylCoA"], label="AcetylCoA")
    plt.title("other metabolomics over time")
    plt.xlabel("Timestep")
    plt.ylabel("Concentration (a.u.)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'Other_history.png')

    # Save history to CSV for inspection
    df.to_csv("./cell_metabolism_history.csv", index_label="timestep")
