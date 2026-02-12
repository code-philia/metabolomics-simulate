# 模拟接口：生物反应函数说明

本文件登记 modules/code/simulate.py 中代表生物反应（含代谢、转运、合成、解毒及信号过程）的函数，提供自然语言名称、功能简述与主要规则。每项均附源码位置以便跳转。

## 代谢反应与转运

- 名称: 己糖激酶 (HK/GK) 反应
  - 源函数: hexokinase_step
  - 输入: 葡萄糖, ATP
  - 输出: G6P, ADP
  - 简述: 葡萄糖入胞磷酸化。
  - 规则: 肝脏葡萄糖激酶(GK)的Km较高(5.0)，受胰岛素高度诱导；速率受血糖和胰岛素共同驱动，基础比例0.2+胰岛素比例0.8；实际速率受葡萄糖(不超过10%)和ATP(不超过50%)限制；单步消耗不超过现有底物的10%和ATP的50%。 

- 名称: 磷酸果糖激酶-1 (PFK-1) 反应
  - 源函数: pfk1_step
  - 输入: G6P, ATP
  - 输出: f16bp, ADP
  - 简述: 限速步骤，决定糖酵解的"流量"。
  - 规则: 增加反馈抑制：F16BP堆积抑制PFK1，抑制系数=1/(1+f16bp/0.5)；ATP是PFK-1的异构抑制剂，当ATP充足时(>3.0)抑制糖酵解流量，抑制系数=1/(1+max(0,atp-3.0)*2.0)；低Km(0.2)确保G6P能被有效向下游拉动；实际速率受G6P和ATP(不超过50%)限制。 

- 名称: 丙酮酸激酶 (PK) 反应
  - 源函数: [pyruvate_kinase_step]
  - 输入: f16bp, ADP, NAD+
  - 输出: 丙酮酸, ATP, NADH
  - 简述: 第二次底物水平磷酸化，产生 ATP。
  - 规则: 

- 名称: 乳酸脱氢酶 (LDH) / 丙酮酸去路反应
  - 源函数: [pyruvate_destination_logic]
  - 输入: 丙酮酸, NADH
  - 输出: 乙酰CoA, 乳酸, NAD+
  - 简述: anaerobically 时，将丙酮酸转换为乳酸。
  - 规则: 受氧气浓度与 NADH 浓度限制；当氧气浓度低于40或 NADH 浓度超过1.0时，将 anaerobically 转换为乳酸。

- 名称: G6P→G1P 变位（PGM）
  - 源函数: [pgm_G6P_to_G1P]
  - 输入: G6P
  - 输出: G1P
  - 激活条件: 受G6P浓度限制（上限2.0）。
  - 简述: 消耗G6P，为糖原合成做准备（简化模型中不直接生成G1P）。
  - 规则: 受可用葡萄糖上限约束，按比例转化。

- 名称: UDP-葡萄糖合成
  - 源函数: [udpGlucoseSynthesis]
  - 输入: G1P, ATP
  - 输出: UDPG, ADP
  - 激活条件: 受G6P与ATP限制。
  - 简述: 生成UDP-葡萄糖，伴随ATP消耗。
  - 规则: 受葡萄糖与ATP共同限制，低比例消耗ATP。

- 名称: 糖原合成酶反应
  - 源函数: [glycogenSynthaseStep]
  - 输入: UDPG
  - 输出: 糖原
  - 激活条件: 胰岛素与胰岛素敏感性促进；受G6P与ATP限制。
  - 简述: 在胰岛素信号驱动下合成糖原。
  - 规则: 速率与胰岛素×敏感性相关；消耗少量ATP并生成等量ADP。

- 名称: 糖原分支酶反应
  - 源函数: [branchingEnzymeStep]
  - 输入: 糖原
  - 输出: 无净物质变化（仅记录速率）
  - 激活条件: 受糖原浓度限制（上限1.0）。
  - 简述: 增加糖原分支结构的步骤。
  - 规则: 受糖原水平与速率修饰限制，影响较小。

- 名称: 糖原磷酸化酶反应
  - 源函数: [glycogenPhosphorylaseStep](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 糖原
  - 输出: 糖原 (消耗), 葡萄糖-6-磷酸 (G6P) (生成)
  - 激活条件: 胰高血糖素与肾上腺素促进；受糖原浓度限制（米氏方程）。
  - 简述: 在胰高血糖素/肾上腺素作用下分解糖原并释放葡萄糖。
  - 规则: 速率与胰高血糖素、肾上腺素水平成正相关。

- 名称: 去分支酶反应
  - 源函数: [debranchingEnzymeStep](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 糖原
  - 输出: 葡萄糖, G1P
  - 激活条件: 受糖原浓度限制（上限1.0）。
  - 简述: 去除糖原分支并产生少量G6P。
  - 规则: 受糖原水平与速率修饰限制。

- 名称: G1P→G6P 转化
  - 源函数: [g1p_to_g6p](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: G1P
  - 输出: G6P
  - 激活条件: 无（速率恒为0）。
  - 简述: 将G1P转回G6P的占位转换。
  - 规则: 当前实现不改变代谢物总量。

- 名称: PEPCK 草酰乙酸→PEP
  - 源函数: [pepck_OAA_to_PEP](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: ATP
  - 输出: ATP (消耗)
  - 激活条件: 受ATP浓度限制。
  - 简述: 糖异生关键步，ATP参与的羧基转移与脱羧。
  - 规则: 受ATP水平与速率修饰限制，消耗ATP。

- 名称: G6P酶生成葡萄糖
  - 源函数: [g6pase_G6P_to_Glucose]
  - 输入: 葡萄糖-6-磷酸 (G6P)
  - 输出: 葡萄糖
  - 激活条件: 受胰岛素抑制；受G6P浓度限制（米氏方程）。
  - 简述: 糖异生/糖原分解末端释放葡萄糖。
  - 规则: 胰岛素越高抑制越强；消耗G6P生成葡萄糖。

- 名称: 脂肪酸合成
  - 源函数: [fattyAcidSynthesis](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 乙酰辅酶A, NADPH, ATP
  - 输出: 乙酰辅酶A (消耗), 脂肪酸 (生成), NADPH (消耗), ATP (消耗)
  - 激活条件: 胰岛素与胰岛素敏感性促进；受底物 (乙酰CoA, NADPH, ATP) 限制。
  - 简述: 胰岛素驱动下以乙酰-CoA与NADPH生成脂肪酸。
  - 规则: 受胰岛素×敏感性与底物限制；消耗NADPH与ATP。

- 名称: 脂肪酸β-氧化
  - 源函数: [betaOxidation](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 脂肪酸, NAD+, 乙醇
  - 输出: 脂肪酸 (消耗), 乙酰辅酶A (生成), NADH (生成), NAD+ (消耗), ATP (生成)
  - 激活条件: 胰高血糖素/肾上腺素促进；酒精抑制；受脂肪酸浓度与NAD+限制。
  - 简述: 脂肪酸分解为乙酰-CoA并生成NADH、ATP。
  - 规则: 受胰高血糖素/肾上腺素促进；酒精抑制；高脂肪酸时提高速率。

- 名称: 新生脂肪生成（DNL）
  - 源函数: [deNovoLipogenesis](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 葡萄糖, ATP, NADPH
  - 输出: 葡萄糖 (消耗), 脂肪酸 (生成), ATP (消耗), NADPH (消耗)
  - 激活条件: 胰岛素与胰岛素敏感性促进；受过量葡萄糖 (>4.0) 驱动。
  - 简述: 高糖时将葡萄糖转化为脂肪酸。
  - 规则: 受胰岛素×敏感性及“过量葡萄糖”驱动；消耗ATP与NADPH。

- 名称: 脂质转运/装载
  - 源函数: [lipidTransport](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 脂肪酸
  - 输出: 脂肪酸 (消耗), 甘油三酯 (生成)
  - 激活条件: 胰岛素与胰岛素敏感性促进；受脂肪酸浓度限制。
  - 简述: 将脂肪酸转为三酯并输出。
  - 规则: 胰岛素×敏感性促进；受脂肪酸可用量限制。

- 名称: 脂肪组织脂解
  - 源函数: [adiposeLipolysis](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 无 (模拟组织释放)
  - 输出: 脂肪酸 (生成), 甘油 (生成)
  - 激活条件: 胰高血糖素/肾上腺素促进；胰岛素抑制 (低胰岛素时增强)。
  - 简述: 释放脂肪酸与甘油。
  - 规则: 胰高血糖素/肾上腺素增强；低胰岛素时额外提升。

- 名称: 氨基酸分解
  - 源函数: [aminoAcidCatabolism](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 氨基酸, ATP
  - 输出: 氨基酸 (消耗), 氨 (生成), ATP (消耗)
  - 激活条件: 进食状态与皮质醇促进；受氨基酸 (>20.0) 与ATP限制。
  - 简述: 生成氨与消耗ATP。
  - 规则: 受进食状态与皮质醇影响；底物与ATP限制。

- 名称: 氨基酸合成与转运（蛋白）
  - 源函数: [aminoAcidSynthesisTransport](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 氨基酸, ATP
  - 输出: 氨基酸 (消耗), 白蛋白 (生成), 凝血因子 (生成), ATP (消耗)
  - 激活条件: 受氨基酸与ATP限制。
  - 简述: 合成白蛋白与凝血因子。
  - 规则: 受氨基酸与ATP双底物限制；按比例分配产物。

- 名称: 氧化磷酸化
  - 源函数: [oxidativePhosphorylation](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: NADH, 氧气, ADP
  - 输出: NADH (消耗), NAD+ (生成), 氧气 (消耗), ATP (生成), ADP (消耗)
  - 激活条件: 受NADH, 氧气, ADP限制。
  - 简述: NADH与氧驱动ATP生成。
  - 规则: 受NADH、氧与ADP限制；NADH→NAD+，ATP↑ADP↓。

- 名称: 酮体生成
  - 源函数: [ketogenesis](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 乙酰辅酶A, 葡萄糖(信号)
  - 输出: 乙酰辅酶A (消耗), 酮体 (生成)
  - 激活条件: 胰高血糖素与低胰岛素促进；受低血糖 (<70.0) 驱动。
  - 简述: 低糖/高胰高血糖素时由乙酰-CoA生成酮体。
  - 规则: 进食状态限制；胰岛素低时增强；速率加以上下限约束。

- 名称: 乳酸发酵
  - 源函数: [lactateFermentation](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 丙酮酸, NADH
  - 输出: 丙酮酸 (消耗), 乳酸 (生成), NADH (消耗), NAD+ (生成)
  - 激活条件: 缺氧 (<40.0) 或 NAD+ 不足时触发。
  - 简述: 丙酮酸还原为乳酸以再生NAD+。
  - 规则: 缺氧或NAD+缺乏时速率显著增加。

- 名称: NAMPT 补救合成 NAD+
  - 源函数: [nampt_Salvage](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 烟酰胺, ATP
  - 输出: 烟酰胺 (消耗), NAD+ (生成), ATP (消耗)
  - 激活条件: 受烟酰胺, ATP, 肝功能限制。
  - 简述: 利用烟酰胺合成NAD+。
  - 规则: 消耗ATP再生NAD+。

- 名称: 从头合成 NAD+
  - 源函数: [deNovoNADSynthesis](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 烟酸, 色氨酸, ATP
  - 输出: 烟酸 (消耗), 色氨酸 (消耗), NAD+ (生成), ATP (消耗)
  - 激活条件: 受烟酸, 色氨酸, ATP, 肝功能限制。
  - 简述: 利用烟酸和色氨酸合成NAD+。
  - 规则: 消耗ATP再生NAD+。

- 名称: CPS1 氨→氨甲酰磷酸 (模拟为瓜氨酸)
  - 源函数: [cps1_Ammonia_to_CarbamoylPhosphate](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 氨, ATP
  - 输出: 氨 (消耗), ATP (消耗), 瓜氨酸 (生成)
  - 激活条件: 进食状态促进；受氨与ATP限制。
  - 简述: 尿素循环起始步，消耗ATP生成瓜氨酸前体。
  - 规则: 进食状态提升；受氨与ATP限制。

- 名称: OTC 合成瓜氨酸 (模拟为精氨酸代琥珀酸)
  - 源函数: [otc_CarbamoylPhosphate_to_Citrulline](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 瓜氨酸, 鸟氨酸
  - 输出: 瓜氨酸 (消耗), 精氨酸代琥珀酸 (生成)
  - 激活条件: 进食状态促进；受瓜氨酸与鸟氨酸限制。
  - 简述: 由氨甲酰磷酸与鸟氨酸生成瓜氨酸。
  - 规则: 受底物最小值限制；进食状态提升。

- 名称: ASS1 生成精氨酸代琥珀酸 (模拟为精氨酸)
  - 源函数: [ass1_Citrulline_to_ASP_Argininosuccinate](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 精氨酸代琥珀酸
  - 输出: 精氨酸代琥珀酸 (消耗), 精氨酸 (生成)
  - 激活条件: 进食状态促进；受底物限制。
  - 简述: 尿素循环中间步。
  - 规则: 受底物与进食状态限制。

- 名称: ASL 生成精氨酸与延胡索酸 (模拟为尿素)
  - 源函数: [asl_Argininosuccinate_to_Arginine_Fumarate](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 精氨酸
  - 输出: 精氨酸 (消耗), 尿素 (生成), 鸟氨酸 (生成)
  - 激活条件: 进食状态促进；受精氨酸限制。
  - 简述: 尿素循环后段，生成尿素前体与再生鸟氨酸。
  - 规则: 受底物与进食状态限制；副产物比例固定。

- 名称: ARG1 精氨酸→尿素/鸟氨酸
  - 源函数: [arg1_Arginine_to_Urea_Ornithine](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 无
  - 输出: 无
  - 激活条件: 无 (速率恒为0)。
  - 简述: 尿素循环末端步（占位）。
  - 规则: 当前实现不改变量。

- 名称: Ⅰ相氧化还原（药物代谢）
  - 源函数: [phaseI_OxRed](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 外源物负荷 (Parameter), NADPH
  - 输出: Ⅰ相中间体 (生成), NADPH (消耗)
  - 激活条件: 受外源负荷, NADPH, 肝功能限制。
  - 简述: 依赖NADPH与肝功能将外源物氧化为中间体。
  - 规则: 受外源负荷、NADPH、肝功能限制。

- 名称: Ⅱ相结合反应
  - 源函数: [phaseII_Conjugation](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: Ⅰ相中间体, UDPGA, PAPS, GSH
  - 输出: Ⅰ相中间体 (消耗), 结合物 (生成/清除), UDPGA (消耗), PAPS (消耗), GSH (消耗)
  - 激活条件: 受中间体, 辅基 (UDPGA/PAPS/GSH), 肝功能限制。
  - 简述: 使用UDPGA/PAPS/GSH与肝功能完成结合与清除。
  - 规则: 受中间体与辅基可用性、肝功能平方项影响；持续清除积累的结合物。

- 名称: 胆红素葡糖醛酸化（UGT）
  - 源函数: [bilirubinUGT](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 间接胆红素, UDPGA
  - 输出: 间接胆红素 (消耗), 直接胆红素 (生成), UDPGA (消耗)
  - 激活条件: 受间接胆红素, UDPGA, 肝功能限制。
  - 简述: 将间接胆红素转为直接胆红素，消耗UDPGA。
  - 规则: 受底物与肝功能限制。

- 名称: 酒精脱氢酶（ADH）
  - 源函数: [ethanol_ADH](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 乙醇, NAD+
  - 输出: 乙醇 (消耗), 乙醛 (生成), NADH (生成), NAD+ (消耗)
  - 激活条件: 受乙醇, NAD+, 肝功能限制。
  - 简述: 乙醇→乙醛并驱动NAD+→NADH。
  - 规则: 受乙醇、NAD+与肝功能限制；直接调整NADH/NAD+。

- 名称: 醛脱氢酶（ALDH）
  - 源函数: [acetaldehyde_ALDH](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 乙醛, NAD+
  - 输出: 乙醛 (消耗), 乙酸 (生成), NADH (生成), NAD+ (消耗)
  - 激活条件: 受乙醛, NAD+, 肝功能, ALDH活性限制。
  - 简述: 乙醛→乙酸并驱动NAD+→NADH。
  - 规则: 受乙醛、NAD+与肝功能限制；直接调整NADH/NAD+。

- 名称: 乙酸→乙酰-CoA 合成
  - 源函数: [acetate_to_acetylcoa](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 乙酸, ATP
  - 输出: 乙酸 (消耗), 乙酰辅酶A (生成), ATP (消耗)
  - 激活条件: 受乙酸, ATP限制。
  - 简述: 乙酸活化生成乙酰-CoA，消耗ATP。
  - 规则: 受乙酸与ATP限制。

- 名称: 胆汁酸合成
  - 源函数: [bileAcidSynthesis](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 胆固醇
  - 输出: 胆固醇 (消耗), 胆汁酸 (生成)
  - 激活条件: 受胆固醇限制。
  - 简述: 由胆固醇生成胆汁酸。
  - 规则: 受胆固醇与速率修饰限制。

- 名称: 血浆蛋白合成
  - 源函数: [plasmaProteinSynthesis](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 氨基酸, ATP
  - 输出: 氨基酸 (消耗), 白蛋白 (生成), ATP (消耗)
  - 激活条件: 进食状态促进；受氨基酸, ATP限制。
  - 简述: 以氨基酸与ATP合成白蛋白。
  - 规则: 进食状态提升；双底物限制。

- 名称: 凝血因子合成
  - 源函数: [coagulationFactorSynthesis](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 氨基酸, ATP
  - 输出: 氨基酸 (消耗), 凝血因子 (生成), ATP (消耗)
  - 激活条件: 受氨基酸, ATP限制。
  - 简述: 以氨基酸与ATP生成凝血因子。
  - 规则: 双底物限制；ATP消耗较低。

- 名称: 胞浆 ATPase 负荷
  - 源函数: [cytosolicATPase_load](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: ATP
  - 输出: ATP (消耗), ADP (生成)
  - 激活条件: 受ATP限制 (上限2.0)。
  - 简述: 非特异ATP水解负荷，转化为ADP。
  - 规则: 受ATP水平与速率修饰限制。

## 信号与调控

- 名称: 系统信号编排
  - 源函数: [orchestrateSystemSignals](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 无
  - 输出: 无
  - 激活条件: 无
  - 简述: 调用激素、神经、免疫信号模块及降解模块。
  - 规则: 编排调用，不直接产生代谢物变化。

- 名称: 能量赤字策略
  - 源函数: [applyEnergyDeficitPolicies](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: ATP, 乙醇
  - 输出: 全局速率修饰符 (Action)
  - 激活条件: ATP < 1.5 或 乙醇 > 0.1。
  - 简述: 根据ATP与乙醇水平下调全局速率。
  - 规则: ATP低时大幅下调 (0.3)；酒精高时轻微下调 (0.8)。

- 名称: 激素信号转导（胰岛素/胰高血糖素）
  - 源函数: [hormoneSignalTransduction](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 葡萄糖
  - 输出: 胰岛素 (生成), 胰高血糖素 (生成)
  - 激活条件: 葡萄糖浓度 (Sigmoid函数)。
  - 简述: 依据血糖生成胰岛素/胰高血糖素信号。
  - 规则: 采用Sigmoid响应；中心值约为5.0mmol/L。

- 名称: 神经信号整合（肾上腺素）
  - 源函数: [neuralSignalIntegration](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 肾上腺素
  - 输出: 肾上腺素 (限幅后)
  - 激活条件: 无
  - 简述: 规范化肾上腺素范围并写回信号。
  - 规则: 限幅到生理区间 [0.05, 2.0]。

- 名称: 免疫信号交互（炎症）
  - 源函数: [immuneSignalInteraction](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 炎症
  - 输出: 炎症 (衰减), 胰岛素敏感性 (调整)
  - 激活条件: 炎症水平。
  - 简述: 缓慢衰减炎症水平并下调胰岛素敏感性。
  - 规则: 炎症越高，敏感性越低（下限0.5）。

- 名称: 胰岛素降解（IDE）
  - 源函数: [degradeInsulin](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 胰岛素, IDE活性
  - 输出: 胰岛素 (减少)
  - 激活条件: IDE活性与胰岛素浓度。
  - 简述: IDE活性驱动胰岛素清除。
  - 规则: 降解速率∝IDE×胰岛素。

- 名称: 胰高血糖素降解
  - 源函数: [degradeGlucagon](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 胰高血糖素
  - 输出: 胰高血糖素 (减少)
  - 激活条件: 无
  - 简述: 基础速率清除胰高血糖素。
  - 规则: 固定幅度衰减。

- 名称: 儿茶酚胺失活
  - 源函数: [inactivateCatecholamines](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 肾上腺素
  - 输出: 肾上腺素 (减少)
  - 激活条件: 无
  - 简述: 基础速率清除肾上腺素。
  - 规则: 固定幅度衰减。

## 流程编排（组合调用）

- 名称: 糖原合成编排
  - 源函数: [orchestrateGlycogenSynthesis](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 无 (调用子函数)
  - 输出: 无 (调用子函数)
  - 激活条件: 胰岛素 > 胰高血糖素
  - 简述: 组合PGM、UDP-Glc、GS与分支酶输出净变化。
  - 规则: 聚合各子反应的产出写入环境。

- 名称: 糖原分解编排
  - 源函数: [orchestrateGlycogenBreakdown](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 无 (调用子函数)
  - 输出: 无 (调用子函数)
  - 激活条件: 胰高血糖素 >= 胰岛素
  - 简述: 组合GP、去分支与G1P→G6P。
  - 规则: 聚合并写入环境。

- 名称: 糖异生编排
  - 源函数: [orchestrateGluconeogenesis]
  - 输入: 乳酸, 甘油, 氨基酸, ATP
  - 输出: G6P
  - 激活条件: 胰高血糖素/皮质醇/炎症促进；酒精抑制；受底物限制。
  - 简述: 汇总乳酸/甘油/氨基酸供体生成葡萄糖。
  - 规则: 酒精抑制；炎症/皮质醇促进；进食状态限幅。

- 名称: 糖酵解编排
  - 源函数: [orchestrateGlycolysis]
  - 输入: 无 (调用子函数)
  - 输出: 无 (调用子函数)
  - 激活条件: 胰高血糖素不显著高于胰岛素。
  - 简述: 组合GK/HK、中间步与PK。
  - 规则: 聚合并写入环境。

- 名称: 脂质代谢编排
  - 源函数: [orchestrateLipidMetabolism](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 胰岛素, 胰高血糖素, 脂肪酸, 甘油三酯
  - 输出: 无 (调用子函数)
  - 激活条件: 激素水平与脂肪酸浓度。
  - 简述: 协调脂肪合成、分解、氧化与转运。
  - 规则: 胰岛素高时促合成；胰高血糖素高或高脂肪酸时促氧化/分解。

- 名称: 氨基酸代谢编排
  - 源函数: [orchestrateAminoAcidMetabolism](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 无 (调用子函数)
  - 输出: 无 (调用子函数)
  - 激活条件: 无
  - 简述: 组合氨基酸分解与合成转运。
  - 规则: 聚合并写入环境。

- 名称: 能量稳态编排
  - 源函数: [orchestrateEnergyHomeostasis](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 葡萄糖
  - 输出: 无 (调用子函数)
  - 激活条件: 葡萄糖浓度
  - 简述: 低糖时产酮，正常时氧化磷酸化。
  - 规则: 血糖 < 4.0 产酮，否则氧化磷酸化。

- 名称: NAD稳态编排
  - 源函数: [orchestrateNADHomeostasis](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 无 (调用子函数)
  - 输出: 无 (调用子函数)
  - 激活条件: 无
  - 简述: 组合NAMPT补救、从头合成与乳酸发酵。
  - 规则: 聚合并写入环境。

- 名称: 尿素循环编排
  - 源函数: [orchestrateUreaCycle](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 无 (调用子函数)
  - 输出: 无 (调用子函数)
  - 激活条件: 无
  - 简述: 组合尿素循环各步骤。
  - 规则: 聚合并写入环境。

- 名称: 解毒流程编排
  - 源函数: [orchestrateDetoxification](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 无 (调用子函数)
  - 输出: 无 (调用子函数)
  - 激活条件: 无
  - 简述: 组合氧化还原、结合反应、酒精代谢与胆红素代谢。
  - 规则: 聚合并写入环境。

- 名称: 合成与分泌编排
  - 源函数: [orchestrateSynthesisSecretion](file:///home/yifei/AI4Science/metabolomics/simulate/modules/code/simulate.py)
  - 输入: 无 (调用子函数)
  - 输出: 无 (调用子函数)
  - 激活条件: 无
  - 简述: 组合胆汁酸、血浆蛋白与凝血因子合成。
  - 规则: 聚合并写入环境。
