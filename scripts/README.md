# 命令入口

从仓库根目录运行。

| 用途 | 入口 |
| --- | --- |
| 路径配置 | `python scripts/configure_paths.py --machine .local/machine.json` |
| EgoSuite 下载与监控 | `datasets/download_egosuite.py`、`datasets/monitor_egosuite.py` |
| EgoExo-4D HM 下载与监控 | `datasets/download_egoexo4d_hm.py`、`datasets/monitor_egoexo4d_hm.py` |
| DINO 特征提取 | `egomotion-pipeline extract-smplh-features` |
| Motion 训练、推理与评估 | `motionexpert-train`、`motionexpert-infer`、`motionexpert-eval` |
| 联合训练 | `VLMExpert/scripts/train/psi0/posttrain-dual-source-unifolm.sh` |
| 仿真与遥操作 | [4090_simple](4090_simple/README.md) |

路径参数见[配置说明](../configs/README.md)，训练与评估示例见[使用指南](../docs/reproduction/README.md)。
下载器使用 `--output-dir` 指定目录；默认根目录为 `CVPR_DATA_ROOT` 或 `~/cvpr-data`。
