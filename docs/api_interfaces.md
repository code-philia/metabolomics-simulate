# 接口文档（依据 modules/docs/requirements.yaml）

本接口文档根据 `modules/docs/requirements.yaml` 的功能与控制条件，定义各模块的函数签名与调用关系。文档不包含实现，仅描述输入/输出、调用链与依赖。路径参考示例：`modules/docs/requirements.yaml:65`。

## 约定与通用类型
- `Ctx`：上下文对象，包含环境读写与控制评估能力
  - `env`: 访问代谢物、信号、参数、隔室
  - `control`: 评估 `control_conditions` 的引擎
- `Metabolites`/`Signals`/`Parameters`: 环境映射
- `Compartment`: 反应所在位置
- 返回值统一为 `{ outputs, effects?, notes? }`

## 全局环境接口（ENV-1）
- 来源：`modules/docs/requirements.yaml:12`
- `getMetabolite(ctx: Ctx, name: string, compartment?: Compartment) -> number`
- `setMetabolite(ctx: Ctx, name: string, value: number, compartment?: Compartment) -> void`
- `getSignal(ctx: Ctx, name: string) -> number`
- `setSignal(ctx: Ctx, name: string, value: number) -> void`
- `getParameter(ctx: Ctx, name: string) -> number`
- `setParameter(ctx: Ctx, name: string, value: number) -> void`
- `writeOutputs(ctx: Ctx, outputs: Metabolites | Signals) -> void`

## 控制条件接口（通用）
- `evaluateControl(ctx: Ctx, ccId: string) -> boolean`
- `applyAction(ctx: Ctx, action: string, payload?: any) -> void`
- 典型调用：各反应函数在执行前后调用 `evaluateControl` 与 `applyAction`

## 营养代谢（REQ-1）
- 来源：`modules/docs/requirements.yaml:51`

### 碳水化合物代谢（REQ-1-1）
- 来源：`modules/docs/requirements.yaml:59`

#### 糖原合成（REQ-1-1-1）
- 来源：`modules/docs/requirements.yaml:65`
- Orchestrator
  - `orchestrateGlycogenSynthesis(ctx: Ctx) -> { outputs }`
  - 调用链：
    - `pgm_G6P_to_G1P(ctx)`
    - `udpGlucoseSynthesis(ctx)`
    - `glycogenSynthaseStep(ctx)`
    - `branchingEnzymeStep(ctx)`
- 反应函数
  - `pgm_G6P_to_G1P(ctx: Ctx) -> { outputs }`
  - `udpGlucoseSynthesis(ctx: Ctx) -> { outputs, notes }`
  - `glycogenSynthaseStep(ctx: Ctx) -> { outputs }`
  - `branchingEnzymeStep(ctx: Ctx) -> { outputs, notes }`

#### 糖原分解（REQ-1-1-2）
- 来源：`modules/docs/requirements.yaml:108`
- Orchestrator
  - `orchestrateGlycogenBreakdown(ctx: Ctx) -> { outputs }`
  - 调用链：
    - `glycogenPhosphorylaseStep(ctx)`
    - `debranchingEnzymeStep(ctx)`
    - `g1p_to_g6p(ctx)`（可复用 PGM 方向）
- 反应函数
  - `glycogenPhosphorylaseStep(ctx: Ctx) -> { outputs }`
  - `debranchingEnzymeStep(ctx: Ctx) -> { outputs }`
  - `g1p_to_g6p(ctx: Ctx) -> { outputs }`

#### 糖异生（REQ-1-1-3）
- 来源：`modules/docs/requirements.yaml:152`
- Orchestrator
  - `orchestrateGluconeogenesis(ctx: Ctx) -> { outputs }`
  - 调用链（示例）：
    - `lactate_to_pyruvate(ctx)`
    - `pepck_OAA_to_PEP(ctx)`
    - `f1_6bp_to_f6p(ctx)`
    - `g6p_to_glucose(ctx)`
- 反应函数（示例）
  - `pepck_OAA_to_PEP(ctx: Ctx) -> { outputs }`
  - `g6pase_G6P_to_Glucose(ctx: Ctx) -> { outputs }`

#### 糖酵解（REQ-1-1-4）
- 来源：`modules/docs/requirements.yaml:206`
- Orchestrator
  - `orchestrateGlycolysis(ctx: Ctx) -> { outputs }`
  - 调用链：
    - `hexokinase_or_glucokinase(ctx)`
    - `pfk1_step(ctx)`
    - `glycolysis_middle_steps(ctx)`
    - `pyruvateKinase_step(ctx)`
- 反应函数
  - `hexokinase_or_glucokinase(ctx: Ctx) -> { outputs }`
  - `pfk1_step(ctx: Ctx) -> { outputs }`
  - `glycolysis_middle_steps(ctx: Ctx) -> { outputs }`
  - `pyruvateKinase_step(ctx: Ctx) -> { outputs }`

### 脂类代谢（REQ-1-2）
- 来源：`modules/docs/requirements.yaml:200`
- Orchestrator
  - `orchestrateLipidMetabolism(ctx: Ctx) -> { outputs }`
  - 调用链：
    - `fattyAcidSynthesis(ctx)` 或 `betaOxidation(ctx)`
    - `lipidTransport(ctx)`
- 反应函数
  - `fattyAcidSynthesis(ctx: Ctx) -> { outputs }`（ACC/FAS）
  - `betaOxidation(ctx: Ctx) -> { outputs }`（含 CPT1 运输前置）
  - `lipidTransport(ctx: Ctx) -> { outputs, effects }`

### 氨基酸代谢（REQ-1-3）
- 来源：`modules/docs/requirements.yaml:312`
- Orchestrator
  - `orchestrateAminoAcidMetabolism(ctx: Ctx) -> { outputs }`
  - 调用链：
    - `aminoAcidCatabolism(ctx)`
    - `aminoAcidSynthesisTransport(ctx)`
- 反应函数
  - `aminoAcidCatabolism(ctx: Ctx) -> { outputs, notes }`
  - `aminoAcidSynthesisTransport(ctx: Ctx) -> { outputs, effects }`

### 能量供应与稳态（REQ-1-4）
- 来源：`modules/docs/requirements.yaml:379`
- Orchestrator
  - `orchestrateEnergyHomeostasis(ctx: Ctx) -> { outputs }`
  - 调用链：
    - `oxidativePhosphorylation(ctx)` 或 `ketogenesis(ctx)`
- 反应函数
  - `oxidativePhosphorylation(ctx: Ctx) -> { outputs, side_products }`
  - `ketogenesis(ctx: Ctx) -> { outputs, notes }`

## 解毒（REQ-2）
- 来源：`modules/docs/requirements.yaml:448`
- Orchestrator
  - `orchestrateDetoxification(ctx: Ctx) -> { outputs }`
  - 调用链：
    - `phaseI_OxRed(ctx)`
    - `phaseII_Conjugation(ctx)`
- 反应函数
  - `phaseI_OxRed(ctx: Ctx) -> { outputs, side_effects }`（CYP450）
  - `phaseII_Conjugation(ctx: Ctx) -> { outputs, effects }`（UGT/SULT/GST）

## 合成与分泌（REQ-3）
- 来源：`modules/docs/requirements.yaml:438`
- Orchestrator
  - `orchestrateSynthesisSecretion(ctx: Ctx) -> { outputs }`
  - 调用链：
    - `bileAcidSynthesis(ctx)`
    - `plasmaProteinSynthesis(ctx)`
    - `coagulationFactorSynthesis(ctx)`
- 反应函数
  - `bileAcidSynthesis(ctx: Ctx) -> { outputs, effects }`
  - `plasmaProteinSynthesis(ctx: Ctx) -> { outputs, effects }`
  - `coagulationFactorSynthesis(ctx: Ctx) -> { outputs, effects }`

## 氮处理与尿素循环（REQ-4）
- 来源：`modules/docs/requirements.yaml:508`
- Orchestrator
  - `orchestrateUreaCycle(ctx: Ctx) -> { outputs }`
  - 调用链（按酶步骤顺序）：
    - `cps1_Ammonia_to_CarbamoylPhosphate(ctx)`
    - `otc_CarbamoylPhosphate_to_Citrulline(ctx)`
    - `ass1_Citrulline_to_ASP_Argininosuccinate(ctx)`
    - `asl_Argininosuccinate_to_Arginine_Fumarate(ctx)`
    - `arg1_Arginine_to_Urea_Ornithine(ctx)`
- 反应函数
  - `cps1_Ammonia_to_CarbamoylPhosphate(ctx: Ctx) -> { outputs }`
  - `otc_CarbamoylPhosphate_to_Citrulline(ctx: Ctx) -> { outputs }`
  - `ass1_Citrulline_to_ASP_Argininosuccinate(ctx: Ctx) -> { outputs }`
  - `asl_Argininosuccinate_to_Arginine_Fumarate(ctx: Ctx) -> { outputs }`
  - `arg1_Arginine_to_Urea_Ornithine(ctx: Ctx) -> { outputs }`

## 激素-神经-免疫调控（REQ-5）
- 来源：`modules/docs/requirements.yaml:540`
- Orchestrator
  - `orchestrateSystemSignals(ctx: Ctx) -> { effects }`
  - 调用链：
    - `hormoneSignalTransduction(ctx)`
    - `neuralSignalIntegration(ctx)`
    - `immuneSignalInteraction(ctx)`
    - `signalDegradationModule(ctx)`（见下）
- 反应函数
  - `hormoneSignalTransduction(ctx: Ctx) -> { effects }`
  - `neuralSignalIntegration(ctx: Ctx) -> { effects }`
  - `immuneSignalInteraction(ctx: Ctx) -> { effects }`

### 信号分子代谢与降解（REQ-5-4）
- 来源：`modules/docs/requirements.yaml:668`
- Orchestrator
  - `signalDegradationModule(ctx: Ctx) -> { effects }`
  - 调用链：
    - `degradeInsulin(ctx)`
    - `degradeGlucagon(ctx)`
    - `inactivateCatecholamines(ctx)`
- 反应函数
  - `degradeInsulin(ctx: Ctx) -> { outputs, effects }`
  - `degradeGlucagon(ctx: Ctx) -> { outputs }`
  - `inactivateCatecholamines(ctx: Ctx) -> { outputs }`

## 能量不足时的统一影响（跨模块）
- 统一入口：`applyEnergyDeficitPolicies(ctx: Ctx) -> void`
- 典型调用点：各 Orchestrator 在开始阶段调用
- 行为：
  - 降低合成途径通量（`fattyAcidSynthesis`, `glycogenSynthaseStep`, `plasmaProteinSynthesis`）
  - 提高分解与供能途径通量（`betaOxidation`, `glycogenBreakdown`, `glycolysis`）
  - 调整控制条件评估：优先满足 `ATP` 与维持生命必需 outputs

## 典型调用图（摘要）
- `orchestrateCarbohydrateMetabolism -> orchestrateGlycogenSynthesis -> pgm -> udpGlucose -> glycogenSynthase -> branching`
- `orchestrateCarbohydrateMetabolism -> orchestrateGlycogenBreakdown -> glycogenPhosphorylase -> debranching -> g1p_to_g6p`
- `orchestrateCarbohydrateMetabolism -> orchestrateGluconeogenesis -> ... -> g6pase`
- `orchestrateCarbohydrateMetabolism -> orchestrateGlycolysis -> hk/gk -> pfk1 -> middle -> pk`
- `orchestrateLipidMetabolism -> fattyAcidSynthesis | betaOxidation -> lipidTransport`
- `orchestrateEnergyHomeostasis -> oxidativePhosphorylation | ketogenesis`
- `orchestrateDetoxification -> phaseI_OxRed -> phaseII_Conjugation`
- `orchestrateUreaCycle -> cps1 -> otc -> ass1 -> asl -> arg1`
- `orchestrateSystemSignals -> hormoneSignalTransduction -> neuralSignalIntegration -> immuneSignalInteraction -> signalDegradationModule`

