# 使用指南

以下命令从仓库根目录执行。先按[路径配置](../../configs/README.md)生成配置文件，将示例中的占位符替换为自己的路径。

## 数据准备

| 输入 | 工具或说明 |
| --- | --- |
| EgoSuite 原始数据 | [下载器](../../datasets/download_egosuite.py)、[监控器](../../datasets/monitor_egosuite.py) |
| EgoExo-4D HM 原始数据 | [下载器](../../datasets/download_egoexo4d_hm.py)、[监控器](../../datasets/monitor_egoexo4d_hm.py) |
| SMPL-H 运动归档、分割与统计 | [MotionExpert](../../MotionExpert/README.md) |
| DINO 视觉特征 | [pipeline](../../pipeline/README.md) |

下载器使用 `--output-dir` 指定目录。

## DINO 特征提取

输入为 SMPL-H 运动归档和对应的原始相机视频，输出为按 episode 保存的特征。

```bash
python -m egomotion_pipeline.cli extract-smplh-features \
  --dataset "<ARCHIVE_ROOT>" \
  --output "<VISION_ROOT>" \
  --config .local/configs/dino.local.json
```

将生成的特征目录填入路径配置的 `vision_profile_root`，然后重新生成配置。

## MotionExpert 训练

输入包括运动归档、数据分割、归一化统计、DINO 特征和窗口缓存。

```bash
python -m MotionExpert.train --config .local/configs/motion.local.json --from-scratch
```

使用 `--devices`、`--batch-size` 和 `--num-workers` 调整训练资源。恢复训练时，用 `--resume "<CHECKPOINT>"` 替换 `--from-scratch`。

## MotionExpert 评估

```bash
python -m MotionExpert.evaluate \
  --checkpoint "<CHECKPOINT>" \
  --config .local/configs/motion.local.json \
  --split val --max-samples "<NUM_SAMPLES>" \
  --output "<OUTPUT_PATH>"
```

通过 `--split` 选择验证集或测试集，`--max-samples` 设置样本数量。推理与 hidden 提取见 [MotionExpert](../../MotionExpert/README.md)。

## 双来源联合训练

复制 [UnifoLM 环境示例](../../configs/machines/unifolm.env.example.sh)，填写数据目录、VLM 权重目录、Motion checkpoint 和 DINO 缓存目录。

```bash
cp configs/machines/unifolm.env.example.sh .local/unifolm.env.sh
# 编辑 .local/unifolm.env.sh
source .local/unifolm.env.sh
bash VLMExpert/scripts/train/psi0/posttrain-dual-source-unifolm.sh
```

模型接口和数据格式见 [VLMExpert](../../VLMExpert/README.md)。
