# 复现入口

本页把数据准备、MotionExpert、双来源训练和仿真评估的入口连接起来。先完成 [安装与本机路径](../setup/README.md)，所有命令均从仓库根目录运行；Bash 示例中的路径变量需要与 `.local/configs/paths.resolved.json` 一致。

## 选择任务

| 任务 | 入口与必要输入 |
| --- | --- |
| 原始数据下载 | [`datasets/`](../../datasets/) 中的下载／监控工具；分别安装所选下载器的 requirements，并检查其 `--help` |
| SMPL-H 归档与质量协议 | [MotionExpert 数据与相机质量说明](../../MotionExpert/README.md#当前数据与相机质量修订)；需要归档、原始来源和独立验收材料 |
| 原生 30Hz DINO 提取 | `egomotion-pipeline extract-smplh-features`；需要已验收运动归档和原始相机视频 |
| 运动模型预训练 | `motionexpert-train`／`python -m MotionExpert.train`；需要完整缓存、统计及训练就绪验收 |
| 运动评估／hidden 提取 | `motionexpert-eval`、`motionexpert-infer`；需要兼容权重、归一化统计及真实历史 DINO |
| 双来源 UnifoLM 后训练 | [本地配方](../../VLMExpert/scripts/train/psi0/posttrain-dual-source-unifolm.sh)；需要显式 VLM、Motion 初始化身份及完整历史缓存 |
| SIMPLE 闭环／PICO 采集 | [运行工具](../../scripts/4090_simple/README.md)、[PICO 指南](../PICO_SIMPLE_TELEOP.md)；需要独立仿真环境和本机资源 |

数据下载完成后仍需完成运动归档、质量验收、DINO、窗口缓存和统计准备。当前仓库没有一个可跳过这些步骤的端到端下载即训练命令。

## DINO 提取计划

以下路径对应默认机器配置。自定义机器配置后同步调整变量。输出选择一个新的仓库外目录，避免覆盖正在使用或已有验收绑定的缓存。

```bash
ARCHIVE_ROOT="$HOME/cvpr-data/MixEgoMotion/smplh-parameters-v4-camera-quality"
NEW_VISION_ROOT="$HOME/cvpr-data/MixEgoMotion/dino-new/psi0_256x480_v1_30hz"
python -m egomotion_pipeline.cli extract-smplh-features \
  --dataset "$ARCHIVE_ROOT" \
  --output "$NEW_VISION_ROOT" \
  --config .local/configs/dino.local.json --dry-run
```

这个 `--dry-run` 检查原始视频来源和提取计划，不加载 DINO、不创建输出。正式提取时移除 `--dry-run`，按本机资源选择 `--gpus` 和 `--workers-per-gpu`。正式使用前需完整验收；诊断子集不能作为完整训练缓存。完成新缓存后，将机器配置的 `vision_profile_root` 指向实际验收目录，再重新生成配置。

已验收、协议匹配的 DINO 缓存可以按现有规则复用，无需仅为目录整理重新提取。详细格式及恢复条件见 [pipeline](../../pipeline/README.md)。

## MotionExpert 训练与评估

生成的 `motion.local.json` 继承现有正式 YAML 配方的非路径参数，替换本机路径。默认配方仍为八卡、每卡 batch256、200 轮；应在运行前确认硬件与数据准备符合任务要求。

数据、分割、统计、窗口缓存及当前代码／架构 GPU 验收就绪后，启动新任务：

```bash
python -m MotionExpert.train --config .local/configs/motion.local.json --from-scratch
```

恢复已有任务时使用显式兼容 checkpoint 和原任务配置，遵循 [MotionExpert 恢复说明](../../MotionExpert/README.md#训练配置与手动命令)。新机器生成配置不意味着旧 checkpoint、缓存或验收报告已完成迁移。

兼容权重和数据已就绪时，可以进行有界验证：

```bash
MOTION_CHECKPOINT="$HOME/cvpr-models/motion/model.ckpt"
EVAL_OUTPUT="$HOME/cvpr-runs/motion/evaluation/val-16.json"
python -m MotionExpert.evaluate \
  --checkpoint "$MOTION_CHECKPOINT" --config .local/configs/motion.local.json \
  --split val --max-samples 16 --seed 62 --output "$EVAL_OUTPUT"
```

这里的模型文件名是本机示例，需替换为实际兼容权重。16 个样本只用于检查评估链路；论文结果应声明完整评估范围、split、seed 和采样设置。`forward_features()` 与 `--features-only` 的用法见 [一步 hidden 接口](../../MotionExpert/README.md#一步hidden与在线共享图像)。

## 双来源 UnifoLM 后训练

使用 [通用机器环境示例](../../configs/machines/unifolm.env.example.sh) 配置本机数据、模型和输出路径。显式选择 EgoDex VLM 权重、兼容 Motion checkpoint、train/val pack ID 及完成的 DINO 缓存；所需变量以配方开头的检查为准。随后可以只检查命令或输入：

```bash
# 在 Bash 中，先设置示例文件要求的本机变量，再加载它。
source configs/machines/unifolm.env.example.sh
bash VLMExpert/scripts/train/psi0/posttrain-dual-source-unifolm.sh --dry-run
bash VLMExpert/scripts/train/psi0/posttrain-dual-source-unifolm.sh --check-only
```

`--dry-run` 打印训练命令；`--check-only` 进一步检查权重、pack 元数据和缓存清单，二者均不启动训练 worker。检查通过后，按 [VLMExpert 配方说明](../../VLMExpert/README.md#unifolm-联合训练配方) 选择正式运行参数。

双来源分支要求六个真实 5Hz 时刻的 DINO 特征，末帧与 VLM 当前帧对齐。单帧官方部署例子不提供这条历史链路；服务端须有真实历史缓冲。当前 `vlm_color_clean_motion` 策略只增强训练中的 VLM 颜色，Motion 使用 clean 历史缓存；完整协议见 [协议索引](../protocols/README.md)。

## 结果与迁移记录

一次可复现实验应保留：代码提交、最终解析配置、初始化权重身份、数据版本与 split、统计／缓存身份、依赖版本、随机种子、硬件与评估范围。大权重和日志保存在仓库外，仓库只保存必要的小型记录与索引。

既有报告中的路径、时间和验收结果描述当时任务。迁移涉及来源路径或文件身份时，按现有协议重新绑定和独立验收；保留旧证据。相关入口见 [实验记录](../experiments/README.md) 和 [迁移说明](../MIGRATION.md)。
