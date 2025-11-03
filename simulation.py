import numpy as np
import matplotlib.pyplot as plt
from tools.reaction import *

class MetabolicSimulation:
    """
    Simulate a simplified metabolic network from modular reaction files and a metabolite pool definition.
    """
    def __init__(self, reaction_folder: str, pool_file: str, auto_adjust=False):
        """
        Initialize the simulation.

        Args:
            reaction_folder (str): Folder containing reaction JSON files.
            pool_file (str): JSON file containing initial metabolite pool.
            auto_adjust (bool): Whether to automatically adjust reaction rates toward steady state.
        """
        self.reactions = load_reactions_from_folder(reaction_folder)
        self.pool = load_pool_from_yaml(pool_file)
        self.auto_adjust = auto_adjust

        self._ensure_pool_consistency()

        # Simulation history
        self.history = {k: [v] for k, v in self.pool.items()}
        self.time = [0]

    def simulate_step(self, dt=1.0):
        """
        Execute one simulation step.
        If auto_adjust=True, reaction capacities are gradually tuned to minimize concentration drift.
        """
        delta = {k: 0 for k in self.pool}
        concentration_change = {}

        for r in self.reactions:
            if not r.substrates:
                rate = r.capacity  # input-only reactions
            else:
                rates = []
                for s, amt in r.substrates.items():
                    if self.pool.get(s, 0) <= 0:
                        rate = 0
                    else:
                        rate = self.pool[s] / (amt * 10.0)
                    rates.append(rate)
                rate = min(min(rates), r.capacity)

            # Apply concentration changes
            if rate > 0:
                for s, amt in r.substrates.items():
                    delta[s] -= amt * rate * dt
                for p, amt in r.products.items():
                    delta[p] = delta.get(p, 0) + amt * rate * dt

            # Optional: record reaction rate change
            concentration_change[r.name] = rate

        # Update metabolite pool
        for k in self.pool:
            self.pool[k] = max(self.pool[k] + delta[k], 0.0)

        # ✅ Ensure new metabolites are tracked
        for k, v in delta.items():
            if k not in self.pool:
                self.pool[k] = 0.0
                self.history[k] = [0.0]
            self.pool[k] = max(self.pool[k] + v, 0.0)

        # Auto-adjust reaction capacity if requested
        if self.auto_adjust:
            self._adjust_reaction_rates(concentration_change)

    def _ensure_pool_consistency(self):
        """
        Ensure all metabolites that appear in reactions exist in the pool.
        Initialize missing ones with zero concentration.
        """
        for r in self.reactions:
            for m in list(r.substrates.keys()) + list(r.products.keys()):
                if m not in self.pool:
                    print(f"[Warning] Metabolite '{m}' not in pool.json — initialized to 0.0")
                    self.pool[m] = 0.0

    def _adjust_reaction_rates(self, concentration_change):
        """
        Adjust reaction capacities gradually to stabilize the system.
        If a metabolite accumulates → slow down producing reactions, speed up consuming reactions.
        """
        for r in self.reactions:
            for p in r.products:
                if self.pool[p] > np.mean(self.history[p]) * 1.2:  # accumulation
                    r.capacity *= 0.98
            for s in r.substrates:
                if self.pool[s] < np.mean(self.history[s]) * 0.8:  # depletion
                    r.capacity *= 1.02

            r.capacity = max(r.capacity, 1e-3)

    def run(self, steps=200, dt=1.0):
        """Run the full simulation."""
        for t in range(steps):
            self.simulate_step(dt)
            for k in self.pool:
                self.history[k].append(self.pool[k])
            self.time.append(t + 1)

    def plot(self, save_fig_path, keys=None):
        """Plot concentration changes over time."""
        if keys is None:
            keys = list(self.pool.keys())

        for k in keys:
            plt.plot(self.time, self.history[k], label=k)

        plt.legend()
        plt.xlabel("Time")
        plt.ylabel("Concentration")
        plt.title("Metabolic Simulation" + (" (auto-adjusted)" if self.auto_adjust else ""))
        plt.show()
        plt.savefig(save_fig_path)


if __name__ == "__main__":
    sim = MetabolicSimulation(
        reaction_folder="reactions",
        pool_file="ini_pool.yaml",
        auto_adjust=True
    )
    sim.run(steps=300)
    sim.plot(save_fig_path='outputs/changes.png',keys=["ATP", "ADP", "NADH", "NAD+", "FADH2", "FAD"])