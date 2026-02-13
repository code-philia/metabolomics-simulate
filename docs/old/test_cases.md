## 测试用例总览（与 YAML 一致）

- 说明覆盖 `modules/docs/test_cases.yaml` 的所有测试用例，提供场景说明、期望变化、覆盖需求与设计依据
- 每个用例在 YAML 中的位置以 `file_path:line_number` 标注，便于跳转

### TC-SLEEP-FASTING-01（过夜禁食） — modules/docs/test_cases.yaml:8
- 场景：外源营养停止，维持血糖与基础能量
- 期望变化：`glucose`轻降，`glycogen`降，`free_fatty_acids`升，`ketone_bodies`基线，`urea`轻升；`insulin`低，`glucagon`高
- 覆盖需求：`REQ-1-1-2`, `REQ-1-1-3`, `REQ-1-2-2`
- 设计依据：早期禁食以糖原分解与糖异生维持血糖

### TC-POSTPRANDIAL-HIGHCARB-01（高碳水餐后） — modules/docs/test_cases.yaml:31
- 场景：餐后胰岛素主导，能量与储存路径增强
- 期望变化：`glucose`短暂升后回落，`glycogen`升，`fatty_acids`经脂肪生成升，`ATP`升；`insulin`高
- 覆盖需求：`REQ-1-1-1`, `REQ-1-1-4`, `REQ-1-2-1`, `REQ-3-2`
- 设计依据：胰岛素促进糖原合成、糖酵解和脂肪酸合成

### TC-EXERCISE-HIGH-INTENSITY-01（高强度运动） — modules/docs/test_cases.yaml:54
- 场景：短时高功率运动，能量快速消耗
- 期望变化：`ATP`降，`AMP`升，`glycogen`快速降，`free_fatty_acids`升，`lactate`升；`adrenaline`高
- 覆盖需求：`REQ-1-1-2`, `REQ-1-1-4`, `REQ-1-2-2`, `REQ-1-4-1`
- 设计依据：AMPK 激活与儿茶酚胺驱动分解途径

### TC-STARVATION-KETOSIS-01（长期饥饿/生酮） — modules/docs/test_cases.yaml:77
- 场景：葡萄糖稀缺，脂肪酸/酮体主供能
- 期望变化：`glucose`低维持，`free_fatty_acids`高，`ketone_bodies`高，`urea`先升后稳；`insulin`极低，`glucagon`高
- 覆盖需求：`REQ-1-1-3`, `REQ-1-2-2`, `REQ-1-4-2`, `REQ-4-1`
- 设计依据：脂肪酸氧化过量驱动酮体生成与糖异生

### TC-HYPOXIA-01（低氧） — modules/docs/test_cases.yaml:101
- 场景：系统性低氧，有氧呼吸受限
- 期望变化：`lactate`升，`ATP`降，`NADH`积累；`adrenaline`中等
- 覆盖需求：`REQ-1-4-1`, `REQ-1-1-4`
- 设计依据：有氧受限时糖酵解增强与乳酸生成

### TC-INFLAMMATION-ACUTE-01（急性炎症） — modules/docs/test_cases.yaml:119
- 场景：细胞因子高，代谢重编程
- 期望变化：`glucose`升，`amino_acids`用于急性期；`insulin_sensitivity`下降，`IL6/TNF_alpha`高
- 覆盖需求：`REQ-5-3`, `REQ-1-1-3`, `REQ-3-2`
- 设计依据：炎症降低胰岛素敏感性并上调蛋白合成

### TC-HIGH-PROTEIN-DIET-01（高蛋白饮食） — modules/docs/test_cases.yaml:139
- 场景：蛋白质摄入高，排氮增强
- 期望变化：`amino_acids`高，`urea`升，`glucose`稳；`insulin`中等
- 覆盖需求：`REQ-1-3-1`, `REQ-4-1`
- 设计依据：氨基酸过剩促分解与尿素循环

### TC-HIGH-FAT-MEAL-01（高脂餐） — modules/docs/test_cases.yaml:157
- 场景：脂类吸收与转运
- 期望变化：`triglycerides/free_fatty_acids/cholesterol_esters`升；`insulin`中等
- 覆盖需求：`REQ-1-2-3`, `REQ-3-1`
- 设计依据：脂蛋白介导转运，胆汁酸支持吸收

### TC-INSULIN-RESISTANCE-01（胰岛素抵抗） — modules/docs/test_cases.yaml:175
- 场景：受体敏感性低，代谢综合征
- 期望变化：`glucose`持续高，`fatty_acids`升，`glycogen`合成下降；`glucagon`相对高
- 覆盖需求：`REQ-5-1`, `REQ-1-1-3`, `REQ-1-2-1`
- 设计依据：胰岛素信号弱化导致合成途径受抑与糖异生未抑制

### TC-CORTISOL-CHRONIC-01（慢性皮质醇升高） — modules/docs/test_cases.yaml:195
- 场景：长期应激激素偏高
- 期望变化：`glucose`升，`amino_acids`肌肉动员，`urea`升；`insulin`中等
- 覆盖需求：`REQ-1-1-3`, `REQ-1-3-1`, `REQ-5-1`
- 设计依据：皮质醇促进糖异生与蛋白分解

### TC-DKA-01（糖尿病酮症酸中毒） — modules/docs/test_cases.yaml:214
- 场景：极低胰岛素、高胰高血糖素与高血糖
- 期望变化：`ketone_bodies`很高，`free_fatty_acids`高，`bicarbonate`降；`adrenaline`中等
- 覆盖需求：`REQ-1-4-2`, `REQ-1-2-2`, `REQ-1-1-3`
- 设计依据：脂肪酸氧化与酮体生成过度导致酸中毒

### TC-REFEEDING-AFTER-FAST-01（断食后再进食） — modules/docs/test_cases.yaml:235
- 场景：长期禁食后高碳水补给
- 期望变化：`glycogen`补充，`ketone_bodies`降，`ATP`升；`insulin`高，`glucagon`抑制
- 覆盖需求：`REQ-1-1-1`, `REQ-1-4-2`, `REQ-1-1-4`
- 设计依据：胰岛素恢复主导，合成与糖酵解增强、酮体抑制

### TC-INSULIN-DEGRADATION-IMPAIRED-01（胰岛素降解受限） — modules/docs/test_cases.yaml:255
- 场景：IDE 活性低导致胰岛素作用延长
- 期望变化：`insulin`长时间高，`glycogen`持续升，`glucose`下降后稳定
- 覆盖需求：`REQ-5-4-1`, `REQ-1-1-1`
- 设计依据：胰岛素清除减弱延长其代谢效应

### TC-LIVER-DETOX-INSUFFICIENCY-01（肝解毒不足） — modules/docs/test_cases.yaml:272
- 场景：肝功能受损下的外源物代谢
- 期望变化：`phaseI_intermediates`积累，`conjugates`降，`NADPH`降；`CYP450_activity`可变
- 覆盖需求：`REQ-2-1`, `REQ-2-2`
- 设计依据：相II能力不足导致中间体堆积与毒性风险升高

### TC-BASELINE-ENV-01（环境稳态基线） — modules/docs/test_cases.yaml:290
- 场景：正常氧分压、pH、温度的稳态
- 期望变化：`glucose/ATP`稳定；`insulin/glucagon`基线
- 覆盖需求：`ENV-1`
- 设计依据：环境读写与稳态验证

### TC-MIXED-MEAL-01（混合营养餐） — modules/docs/test_cases.yaml:308
- 场景：同时摄入碳水/脂肪/蛋白
- 期望变化：`glycogen`升，`fatty_acids`经脂肪生成升，`amino_acids`升、`urea`微升；`insulin`高、`glucagon`低
- 覆盖需求：`REQ-1`, `REQ-1-1`, `REQ-1-2`, `REQ-1-3`
- 设计依据：三大营养素的协同代谢与调控

### TC-HEPATIC-DETOX-GENERAL-01（一般外源物暴露） — modules/docs/test_cases.yaml:331
- 场景：肝功能正常的解毒过程
- 期望变化：`phaseI_intermediates/conjugates`升，`NADPH`降；`CYP450_activity`升
- 覆盖需求：`REQ-2`, `REQ-2-1`, `REQ-2-2`
- 设计依据：相I/II综合验证

### TC-PLASMA-PROTEIN-SYNTHESIS-01（血浆蛋白合成） — modules/docs/test_cases.yaml:350
- 场景：氨基酸与能量充足
- 期望变化：`plasma_proteins`升；`insulin`中等
- 覆盖需求：`REQ-3`, `REQ-3-2`
- 设计依据：合成与分泌在营养充足时上调

### TC-COAGULATION-UPREG-01（凝血因子上调） — modules/docs/test_cases.yaml:366
- 场景：出血存在，维生素K可用
- 期望变化：`coagulation_factors`升；`coagulation_signal`高
- 覆盖需求：`REQ-3`, `REQ-3-3`
- 设计依据：损伤信号驱动维生素K依赖凝血因子合成

### TC-AMMONIA-SPIKE-01（急性氨升高） — modules/docs/test_cases.yaml:382
- 场景：氨浓度急升且ATP充足
- 期望变化：`urea`升；`urea_cycle_activation`高
- 覆盖需求：`REQ-4`, `REQ-4-1`
- 设计依据：高氨诱导尿素循环关键酶活性

### TC-MULTI-SIGNAL-INTEGRATION-01（多信号整合） — modules/docs/test_cases.yaml:398
- 场景：胰岛素/胰高血糖素/肾上腺素/细胞因子并存
- 期望变化：`glucose`可变，`fatty_acids/amino_acids`动员；`insulin_sensitivity`轻度下降
- 覆盖需求：`REQ-5`, `REQ-5-1`, `REQ-5-2`, `REQ-5-3`, `REQ-5-4`
- 设计依据：激素-神经-免疫信号的系统性整合效应

### TC-PFK1-REGULATION-01（PFK-1 限速步调控） — modules/docs/test_cases.yaml:421
- 场景：高ATP/高柠檬酸、低F2,6BP
- 期望变化：`glycolytic_flux`降，`F1_6BP`降
- 覆盖需求：`REQ-1-1-4-2`
- 设计依据：能量与代谢物对 PFK-1 的变构调控

### TC-GLYCOGEN-BRANCHING-THRESH-01（糖原分支阈值） — modules/docs/test_cases.yaml:437
- 场景：直链长度足够且底物充足
- 期望变化：`branched_glycogen`升
- 覆盖需求：`REQ-1-1-1-4`
- 设计依据：链长阈值触发分支酶反应，增加非还原末端

### TC-NORMAL-THREE-MEALS-01（正常一日三餐） — modules/docs/test_cases.yaml:1
- 场景：早餐/午餐/晚餐的常规摄入与代谢响应
- 期望变化：早餐、午餐、晚餐后`glucose`短暂升后回落；`glycogen`净升；`triglycerides`餐后升；夜间空腹`ketone_bodies`相对升；`insulin`餐后高、`glucagon`空腹高
- 覆盖需求：`REQ-1-1-1`, `REQ-1-2-1`, `REQ-3-2`, `ENV-1`
- 设计依据：餐后胰岛素主导合成与储存，夜间空腹脂肪动员与轻度酮生成
