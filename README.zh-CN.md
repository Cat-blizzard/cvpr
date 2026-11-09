# Σ₀：从人类交互与运动到人形机器人移动操作

[English](README.md) | **简体中文**

## 摘要

人形机器人移动操作要求机器人在不同初始状态下调整全身运动，同时保持手与物体之间的交互。采集同步的全身遥操作示范成本高昂，而第一视角视频能够在不同动作粒度上提供可扩展的监督：精细的手腕和指尖轨迹刻画物体交互，稀疏的骨骼运动则描述全身协调。这种监督与执行之间的不对称性促使我们分别学习两类先验，并在机器人控制中将其耦合。我们提出视觉—语言—动作框架 Σ₀，通过手部动作预测学习交互先验，并通过联合重建已观测的骨骼运动与预测其未来演化来学习协调先验。在机器人数据监督的后训练阶段，策略通过以本体感知为条件的串行交叉注意力融合两类先验，直接预测机器人原生的身体和手部动作，无需对人体运动进行重定向。在 SIMPLE 的六项任务上，Σ₀ 的成功率达到 92.8%，较最强基线高出 8.1 个百分点。每项任务使用 10 条示范时，Σ₀ 的成功率达到 83.3%；未进行人类先验预训练的变体在每项任务使用 100 条示范时，成功率为 75.0%。这些结果支持通过互补的人类先验实现高数据效率的人形机器人控制。

## 安装

## 路径配置

使用默认目录生成配置：

```bash
python scripts/configure_paths.py
```

默认目录为 `~/sigma0/data`、`~/sigma0/models` 和 `~/sigma0/runs`。

工具在 `.local/configs/` 下生成以下文件：

| 文件 | 用途 |
| --- | --- |
| `motion.local.json` | MotionExpert 训练与评估配置。 |
| `dino.local.json` | DINO 特征提取配置。 |
| `psi.local.env` | 合并到 `VLMExpert/.env` 的路径变量。 |
| `paths.resolved.json` | 解析后的数据、模型和输出路径。 |

`--dry-run` 用于预览路径，`--output-dir` 指定其他配置目录，`--force` 覆盖已有配置文件。

<details>
<summary>自定义路径</summary>

需要使用其他目录时，复制示例，修改 `data_root`、`model_root` 和 `run_root`，然后重新生成配置：

```bash
mkdir -p .local
cp configs/machines/local.example.json .local/machine.json
# 编辑 .local/machine.json。
python scripts/configure_paths.py --machine .local/machine.json --force
```

还可为以下资源单独指定路径：

| 字段 | 资源 |
| --- | --- |
| `archive_root` | SMPL-H 运动归档。 |
| `stats_path` | 运动归一化统计。 |
| `vision_profile_root` | DINO 特征目录。 |
| `window_cache_root` | 运动训练窗口缓存。 |
| `motion_output_dir` | 运动训练输出目录。 |
| `dino_checkpoint` | 已存在的本地 DINO 模型目录；省略时使用固定版本的官方模型。 |

相对路径以机器 JSON 文件所在目录为基准。路径支持 `~`、`$NAME` 和 `${NAME}`。Motion 归档路径的优先级依次为 `--data-dir`、`MOTIONEXPERT_DATA_DIR`、配置文件。

自定义配置再次生成时，继续传入同一份 `--machine` 文件；下方数据准备命令也使用对应的目录。

</details>

## 数据准备

下载原始数据：

```bash
python datasets/download_egosuite.py run \
  --output-dir "$HOME/sigma0/data/EgoSuite"

python datasets/download_egoexo4d_hm.py \
  --output-dir "$HOME/sigma0/data/EgoExo-4D-HM"
```

HM 下载器使用已配置的 AWS 凭据。下载量、数据选择和账户选项（`--hours`、`--take`、`--aws-profile`）见各脚本的 `--help`。

运动训练需要 SMPL-H 归档、数据分割、归一化统计、DINO 特征和窗口缓存。归档与缓存的准备方法见 [MotionExpert](MotionExpert/README.md)，模型输入见[数据格式](docs/protocols/README.md)。

使用归档及对应的原始相机视频提取 DINO 特征：

```bash
ARCHIVE_ROOT="$HOME/sigma0/data/MixEgoMotion/smplh-parameters-v4-camera-quality"
VISION_ROOT="$ARCHIVE_ROOT/vision_profiles/psi0_256x480_v1_30hz"

python -m egomotion_pipeline.cli extract-smplh-features \
  --dataset "$ARCHIVE_ROOT" \
  --output "$VISION_ROOT" \
  --config .local/configs/dino.local.json
```

该输出目录与默认运动模型配置一致。提取参数见 [pipeline](pipeline/README.md)。

## 训练

### MotionExpert

```bash
python -m MotionExpert.train --config .local/configs/motion.local.json --from-scratch
```

该配方默认使用 8 个 GPU、每卡 batch256。可通过 `--devices`、`--batch-size` 和 `--num-workers` 调整训练资源。

从最近保存的 checkpoint 恢复训练：

```bash
MOTION_RUN="$HOME/sigma0/runs/motion/smplh_k12_psi0_256x480_5hz_camera_quality_v4_meanpool_from_scratch"

python -m MotionExpert.train --config .local/configs/motion.local.json \
  --resume "$MOTION_RUN/last.ckpt"
```

### 双来源动作专家

将 EgoDex 预训练的 VLM 权重放在 `~/sigma0/models/egodex-vlm`。[UnifoLM 环境示例](configs/machines/unifolm.env.example.sh) 默认使用运动训练输出的 `final.ckpt` 和 `~/sigma0/data/UnifoLM` 下的数据：

```bash
cp configs/machines/unifolm.env.example.sh .local/unifolm.env.sh
source .local/unifolm.env.sh
bash VLMExpert/scripts/train/psi0/posttrain-dual-source-unifolm.sh
```

需要使用其他权重或数据集时，调整 `.local/unifolm.env.sh`。双来源策略使用 6 个真实的 5Hz DINO 观测，末帧与 VLM 图像对齐。模型与训练参数见 [VLM Expert](VLMExpert/README.md)。

## 评估

运动训练完成后，评估最终 checkpoint：

```bash
MOTION_RUN="$HOME/sigma0/runs/motion/smplh_k12_psi0_256x480_5hz_camera_quality_v4_meanpool_from_scratch"

python -m MotionExpert.evaluate \
  --checkpoint "$MOTION_RUN/final.ckpt" \
  --config .local/configs/motion.local.json \
  --split val --max-samples 16 \
  --output "$HOME/sigma0/runs/evaluation/motion-val.json"
```

该命令评估 16 个验证窗口。可通过 `--checkpoint`、`--split` 和 `--max-samples` 调整评估对象与规模。运动推理与 hidden 特征提取见 [MotionExpert](MotionExpert/README.md)。

模型服务与仿真见 [SIMPLE 工具](scripts/4090_simple/README.md)，PICO 录制步骤见[遥操作](docs/teleoperation.md)。

## 代码结构

| 组件 | 说明 |
| --- | --- |
| [MotionExpert](MotionExpert/README.md) | 人类运动先验与运动预测。 |
| [ImageProcess](ImageProcess/README.md) | 共享图像预处理与数据增强。 |
| [pipeline](pipeline/README.md) | DINO 特征提取。 |
| [VLM Expert](VLMExpert/README.md) | 视觉语言骨干网络与双来源动作专家。 |

## 致谢

本项目基于 [Ψ₀](https://github.com/physical-superintelligence-lab/Psi0) 构建。第三方代码来源与许可证见[第三方代码](docs/dependencies/README.md)。
