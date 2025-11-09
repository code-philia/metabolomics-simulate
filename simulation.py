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

        # 历史记录：代谢物浓度随时间变化
        self.history = {k: [v] for k, v in self.pool.items()}
        # 反应速率随时间变化
        self.rate_history = {r.name: [] for r in self.reactions}
        self.time = [0]

    def simulate_step(self, dt=1.0):
        """
        Execute one simulation step.
        If auto_adjust=True, reaction capacities are gradually tuned to minimize concentration drift.
        """
        delta = {k: 0 for k in self.pool}

        for r in self.reactions:
            # 计算当前反应速率
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

            # 应用反应变化
            if rate > 0:
                for s, amt in r.substrates.items():
                    delta[s] -= amt * rate * dt
                for p, amt in r.products.items():
                    delta[p] = delta.get(p, 0) + amt * rate * dt

            # 记录速率变化历史
            self.rate_history[r.name].append(rate)

        # 更新代谢池
        for k in self.pool:
            self.pool[k] = max(self.pool[k] + delta[k], 0.0)

        # 确保代谢物存在
        for k, v in delta.items():
            if k not in self.pool:
                self.pool[k] = 0.0
                self.history[k] = [0.0]
            self.pool[k] = max(self.pool[k] + v, 0.0)

        # 可选：自动调节速率
        if self.auto_adjust:
            self._adjust_reaction_rates()

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

    def _adjust_reaction_rates(self):
        """
        Adjust reaction capacities based on recent rate trends.
        If a reaction rate keeps increasing -> downregulate (possible accumulation)
        If a reaction rate keeps decreasing -> upregulate (possible depletion)
        """
        for r in self.reactions:
            recent_rates = self.rate_history[r.name][-5:]  # 最近5步
            if len(recent_rates) >= 2:
                # 计算速率变化趋势
                trend = np.mean(np.diff(recent_rates))
                if trend > 0.01:
                    r.capacity *= 0.98  # 速率在上升 → 轻微抑制
                elif trend < -0.01:
                    r.capacity *= 1.02  # 速率在下降 → 轻微促进

            # 防止 capacity 过低
            r.capacity = max(r.capacity, 1e-3)

    def run(self, steps=200, dt=1.0):
        """Run the full simulation."""
        for t in range(steps):
            self.simulate_step(dt)
            for k in self.pool:
                self.history[k].append(self.pool[k])
            self.time.append(t + 1)

    def plot_rates(self, save_fig_path=None, keys=None):
        # 反应速率可视化
        """Plot the rate evolution of each reaction."""
        if keys is None:
            keys = list(self.rate_history.keys())

        plt.figure(figsize=(8, 5))
        for k in keys:
            plt.plot(self.time[:-1], self.rate_history[k], label=k)
        plt.legend()
        plt.xlabel("Time")
        plt.ylabel("Reaction rate")
        plt.title("Reaction Rate Evolution")
        plt.tight_layout()
        if save_fig_path:
            plt.savefig(save_fig_path)
        plt.show()

    def plot(self, save_fig_path=None, keys=None):
        """Plot concentration changes over time."""
        if keys is None:
            keys = list(self.pool.keys())

        for k in keys:
            plt.plot(self.time, self.history[k], label=k)

        plt.legend()
        plt.xlabel("Time")
        plt.ylabel("Concentration")
        plt.title("Metabolic Simulation" + (" (auto-adjusted)" if self.auto_adjust else ""))
        if save_fig_path:
            plt.savefig(save_fig_path)
        plt.show()


if __name__ == "__main__":
    suffix = ""
    sim = MetabolicSimulation(
        reaction_folder=f"{suffix}reactions",
        pool_file=f"ini_pools/{suffix}ini_pool.yaml",
        auto_adjust=True
    )
    sim.run(steps=500)
    sim.plot(save_fig_path=f'outputs/{suffix}changes.png',keys=["ATP", "ADP", "NADH", "NAD+", "FADH2", "FAD"])
    sim.plot_rates(save_fig_path=f'outputs/{suffix}rates.png')