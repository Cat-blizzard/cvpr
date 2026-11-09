# 命令入口

从仓库根目录运行下列入口。完整环境、资源与验收前提见[安装](../docs/setup/README.md)和[复现指南](../docs/reproduction/README.md)。

| 用途 | 当前入口 | 说明 |
| --- | --- | --- |
| 本机路径配置 | `python scripts/configure_paths.py --machine configs/machines/local.example.json --dry-run` | 先预览；去掉 `--dry-run` 才写入本机配置 |
| EgoSuite 下载与监控 | `datasets/download_egosuite.py`、`datasets/monitor_egosuite.py` | 显式 `--output-dir`，或 `CVPR_DATA_ROOT/EgoSuite`，默认 `~/cvpr-data/EgoSuite` |
| EgoExo-4D HM 下载与监控 | `datasets/download_egoexo4d_hm.py`、`datasets/monitor_egoexo4d_hm.py` | 显式 `--output-dir`，或 `CVPR_DATA_ROOT/EgoExo-4D-HM`，默认 `~/cvpr-data/EgoExo-4D-HM` |
| DINO 特征提取 | `egomotion-pipeline extract-smplh-features` | 使用生成的 `.local/configs/dino.local.json`；来源、时间及视觉身份仍需验收 |
| Motion 训练、推理与评估 | `motionexpert-train`、`motionexpert-infer`、`motionexpert-eval` | 由模块 `pyproject.toml` 注册，详见 [MotionExpert](../MotionExpert/README.md) |
| 联合训练 | `VLMExpert/scripts/train/psi0/posttrain-dual-source-unifolm.sh` | 环境示例见 [unifolm.env.example.sh](../configs/machines/unifolm.env.example.sh)；先 `--dry-run` |
| 仿真、采集、遥操作与交接 | [4090_simple/README.md](4090_simple/README.md) | 保留既有路径和测试；专题索引见[实验记录](../docs/experiments/README.md) |

下载器的文件锁与进程监控依赖 Linux；更改默认路径不代表已完成 Windows 下载环境适配。
已有下载任务在新进程中应继续显式指定原 `--output-dir`，避免默认目录变更后读取另一份状态。

`4090_simple` 中的 A100 任务和历史 campaign 入口仍按原任务身份管理。新的通用入口逐组抽取，
避免一次移动破坏裸模块导入、源码哈希和已保存的调用记录。当前核心训练源码、缓存协议和第三方目录均保留原位。
