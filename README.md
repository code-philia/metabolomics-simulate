# Metabolic Simulation Framework

This project simulates simplified metabolic networks using modular, human-readable definitions.

---

## 🚀 Features
- Modular reaction definitions (`.yaml`)
- Metabolite pool initialization (`.yaml`)
- Time-step simulation with concentration tracking
- Optional automatic adjustment of reaction rates to reach steady state

---

## 🧱 File Structure

project/
├── simulation.py
├── tools/
│ ├── reaction.py
│ └── utils.py
├── reactions/
│ ├── glycolysis_step1.yaml
│ └── oxidative_phosphorylation.yaml
│ └── ...
└── ini_pool.yaml

---

## 🧬 Example Run

```bash
python simulation.py
