# Liver Metabolism Simulator (肝脏代谢模拟工具)

本项目是一个高度自动化、基于大型语言模型（LLM）驱动的肝脏代谢模拟工具。它利用 LLM 的知识库和推理能力，自动生成、细化肝脏代谢的输入/输出数据、条件和参数，并构建运行模拟代码，以实现对真实肝脏代谢流的精确模拟。

## 🌟 项目核心特性

- **LLM 驱动的知识建模**：利用 LLM 从高粒度到低粒度自动细化代谢模块（如从“碳水代谢”细化到“糖异生”）。
- **生产者-消费者模型**：基于代谢物共享资源池，模拟肝脏内复杂的并行代谢反应。
- **多维度生理模拟**：覆盖糖、脂、蛋白质、能量、辅酶、解毒及信号调控（胰岛素、胰高血糖素等）等多个生理过程。
- **交互式可视化面板**：生成动态 HTML 仪表盘，直观展示代谢物浓度波动与反应速率变化。
- **病理场景模拟**：支持非酒精性脂肪肝 (NAFLD)、酒精性代谢障碍等病理状态的模拟与分析。

## 📂 目录结构

```text
.
├── code/                   # 核心代码
│   ├── simulate.py         # 核心模拟引擎，定义环境与代谢反应逻辑
│   ├── vis-nafld.py        # NAFLD 场景模拟与交互式可视化脚本
│   ├── vis-ethanol.py      # 酒精代谢模拟与可视化
│   ├── vis.py              # 通用可视化工具
│   └── sum_result.py       # 结果汇总分析
├── docs/                   # 项目文档
│   ├── detailed_requirements.md  # 详细功能需求文档
│   ├── simulate_funcs_explan.md  # 代谢反应函数的详细生物学说明
│   ├── api_interfaces.md         # API 接口说明
│   ├── ill_cases.md              # 病理案例定义
│   ├── metabolite_constraints.yaml # 代谢物约束配置
│   └── requirements.yaml         # 模块需求定义
├── figs/                   # 文档辅助图片
├── results-html/           # 模拟生成的交互式可视化报告 (HTML)
├── prompts.yaml            # LLM 知识提取与代码生成的提示词
└── PRD.md                  # 产品需求文档
```

## 🚀 核心功能模块

### 1. 代谢环境 (Metabolic Environment)
在 [simulate.py](file:///home/yifei/AI4Science/metabolomics/simulate/code/simulate.py) 中定义了 `MetabolicEnvironment` 类，管理：
- **代谢物池**：包含血糖、糖原、脂肪酸、ATP、NADH、氨、尿素等关键物质。
- **信号系统**：胰岛素、胰高血糖素、肾上腺素、皮质醇及炎症因子。
- **生理参数**：氧分压、pH、温度、肝功能状态等。

### 2. 代谢反应集群
项目实现了数十种精细的生物化学反应函数，详细说明见 [simulate_funcs_explan.md](file:///home/yifei/AI4Science/metabolomics/simulate/docs/simulate_funcs_explan.md)：
- **碳水化合物**：糖酵解、糖异生、糖原合成与分解。
- **脂类代谢**：脂肪酸合成 (FAS)、β-氧化、新生脂肪生成 (DNL)、脂质转运。
- **氮代谢**：氨基酸分解、尿素循环 (CPS1, OTC, ASS1, ASL)。
- **能量与辅酶**：氧化磷酸化、NAD+ 补救/从头合成。
- **解毒系统**：酒精代谢 (ADH/ALDH)、Ⅰ/Ⅱ相解毒、胆红素转化。

### 3. 模拟与可视化
通过 [vis-nafld.py](file:///home/yifei/AI4Science/metabolomics/simulate/code/vis-nafld.py) 等脚本，用户可以：
- 运行特定病例（如 `normal` 或 `nafld`）的 24 小时生理模拟。
- 自动检测反应速率的**震荡 (Oscillation)**，评估模型的稳定性。
- 生成包含“关键代谢物浓度”和“关键反应速率”两个维度的动态 Plotly 图表。

## 🛠 快速开始

### 环境要求
- Python 3.8+
- 依赖库：`numpy`, `pandas`, `plotly`, `pyyaml`

### 运行模拟
运行 NAFLD 模拟并查看可视化结果：
```bash
python code/vis-nafld.py
```
生成的报告将保存在 `results-html/nafld_simulation.html`。

## 📖 技术细节与设计

项目遵循三个阶段的自动化流程：
1. **阶段 I：知识提取**：LLM 生成结构化元数据 ([prompts.yaml](file:///home/yifei/AI4Science/metabolomics/simulate/prompts.yaml))。
2. **阶段 II：模型构建**：自动映射元数据为生产者-消费者代码结构。
3. **阶段 III：调优迭代**：对比真实生理数据（如 [metabolite_constraints.yaml](file:///home/yifei/AI4Science/metabolomics/simulate/docs/metabolite_constraints.yaml)），自动微调动力学参数 $V_{max}$ 和 $K_m$。

---
*本项目旨在为代谢组学研究提供一个可解释、可调优的计算模拟框架。*
