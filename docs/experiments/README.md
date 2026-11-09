# 实验与验收记录索引

本页为已有记录建立导航，原文件保留原位。各记录中的日期、代码、数据、权重和检查范围共同界定结论；机器路径和“当前进度”属于记录时的上下文，本索引不提供实时训练状态。

新环境的规范入口见 [复现说明](../reproduction/README.md)，本机目录设置见 [路径配置](../../configs/README.md)。

## 训练与接口验收

| 内容 | 原始记录 |
| --- | --- |
| Handover 任务适配、初始化、保存与恢复 | [A100 任务记录](../A100_SIMPLE_TASK50_FINETUNE.md) |
| 双来源动作接口 | [Action 验收](../dual_source_action_validation.json)、[联合训练验收](../dual_source_joint_validation.json) |
| VLM token 池化 | [池化验收](../vlm_pooling_validation.json) |
| UnifoLM 完整模型、保存恢复与冷加载 | [完整模型验收](../unifolm_full_model_validation.json) |
| UnifoLM 八卡 batch16 | [八卡验收](../unifolm_8gpu_batch16_validation.json) |
| UnifoLM 启动检查 | [历史启动记录](../unifolm_training_start.json) |
| UnifoLM VLM 颜色增强策略 | [视觉策略验收](../unifolm_vlm_color_validation.json) |
| 提速准备与恢复 | [准备记录](../unifolm_speedup_preparation_validation.json)、[恢复验收](../unifolm_speedup_resume_validation.json) |
| A100 任务初始化 | [40k 初始化记录](../a100_task50_joint40k_validation.json)、[38k 初始化记录](../a100_task50_joint38000_validation.json) |
| 融合 AdamW 对照 | [优化器验收](../a100_fused_adamw_validation.json) |

MotionExpert 的先验探测与 token 读出说明仍在 [模块文档](../../MotionExpert/README.md#冻结运动先验验证) 和 [完整 token 对照](../../MotionExpert/README.md#完整token等参数读出对照)。

## 数据准备与采集

| 内容 | 原始记录 |
| --- | --- |
| UnifoLM 原生 DINO 特征 | [DINO 验收](../unifolm_dino_validation.json) |
| Handover 来源、质量与重新采集 | [质量记录](../HANDOVER_QUALITY100.md) |
| 随机化 100 条采集与准入 | [采集流程](../../scripts/4090_simple/README_handover_random100.md) |
| 按失败阶段增强训练数据 | [数据增强记录](../HANDOVER_FAILURE_GUIDED_DATA_V2.md) |
| 149 条训练与多保存点评测 | [实验流程](../../scripts/4090_simple/README_campaign.md)、[评测入口](../../scripts/4090_simple/README_handover149_eval.md) |

## 部署、资源交接与物理评估

| 内容 | 原始记录 |
| --- | --- |
| 4090 测评需求与协议 | [交接说明](../4090_SIMPLE_HANDOFF.md) |
| 双环境安装的实际检查 | [环境记录](../4090_SIMPLE_ENVIRONMENT.md) |
| A100 → 4090 的 20k 资源 | [资源交接](../4090_SIMPLE_TRANSFER.md) |
| 20k 模型与 SIMPLE 链路检查 | [GPU 与物理检查](../4090_SIMPLE_GPU_ACCEPTANCE.md) |
| CarryBox 本地适配 | [CarryBox 记录](../4090_SIMPLE_CARRYBOX_FINETUNE.md) |
| 独立举箱保持任务 | [LiftBox 记录](../4090_SIMPLE_LIFTBOX_FINETUNE.md) |
| 任务 6000 步、五条 Handover 原 VAL 场景 | [逐条评估证据](../a100_task6000_local_handover_evaluation.json)、[解释与边界](../A100_SIMPLE_TASK50_FINETUNE.md#任务6000步导出与本机handover物理测评) |

接触标志、完整释放、任务完成率、无跌倒和环境成功启动是不同检查项，读取结果时应保留原记录的判定范围。

## 遥操作与故障恢复

| 内容 | 原始记录 |
| --- | --- |
| PICO 4 → SONIC v1.1 → SIMPLE 采集 | [遥操作说明与检查记录](../PICO_SIMPLE_TELEOP.md) |
| 两次原生 CUDA 断言 | [故障分析](../unifolm_assert_recovery_analysis.md) |
| 首轮修复与重启 | [修复验收](../unifolm_assert_repair_validation.json) |
| 后续恢复与诊断快照 | [恢复验收](../unifolm_assert_recovery_validation.json) |

故障记录中的短时恢复成功具有明确检查范围；尚未定位的根因继续沿用原记录的限制。

## 来源与历史快照

- [2026-11-09 首页快照](../archive/README-2026-11-09.md) 保留本轮整理前的完整首页。
- [原代理协议快照](../archive/AGENTS-protocol-2026-11-09.md) 保留原任务状态与数据模型约定，不代表新任务授权。
- [环境与数据迁移](../MIGRATION.md) 记录原迁移方式和展开依赖约定。
- [Ψ₀ 固定上游清单](../psi0_upstream.json) 记录上游版本与本地扩展。
- [2026-10-06 文件汇总](../inventory/summary.json)、[文件清单](../inventory/files.csv)、[依赖清单](../inventory/upstream_dependencies.json) 为初次迁移的历史 inventory。
