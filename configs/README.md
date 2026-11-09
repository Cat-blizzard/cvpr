# 机器路径与实验配置

本目录提供面向 Ubuntu 的公开机器路径示例。模型和数据协议仍由各模块的配置维护；实验配方与机器路径分开管理。
`scripts/configure_paths.py` 从现有 Motion 正式配方和 DINO 示例生成本地配置，只替换路径，不改变架构、损失、学习率、batch 或验收逻辑。

## 快速使用

在仓库根目录预览默认布局：

```bash
python scripts/configure_paths.py --machine configs/machines/local.example.json --dry-run
```

示例中的 `~` 在每位使用者的本机展开，数据、模型和运行目录分别为 `~/cvpr-data`、`~/cvpr-models`、`~/cvpr-runs`。
需要自定义时，复制该文件为 `configs/machines/workstation.local.json`，修改自己的路径后运行：

```bash
python scripts/configure_paths.py --machine configs/machines/workstation.local.json --dry-run
python scripts/configure_paths.py --machine configs/machines/workstation.local.json
```

生成器只需 Python 3.10+ 和 PyYAML；不需要导入 Torch 或加载模型。PyYAML 已包含在 MotionExpert 依赖中，也可单独安装：

```bash
python -m pip install PyYAML
```

`--dry-run` 仅打印已解析的路径和拟生成文件，不创建数据、缓存或输出目录，也不执行训练。
去掉该参数后，默认写入仓库内被忽略的 `.local/configs/`；可以用 `--output-dir` 指定其它配置目录。
已有同名文件时会停止，明确指定 `--force` 才会替换。修改机器文件后重新生成即可。

## 机器文件字段

机器配置是一个 JSON 对象，不接受未定义字段。相对路径以**机器文件所在目录**为基准；`--output-dir` 的相对路径以当前工作目录为基准。
路径支持 `~`、`$NAME`、`${NAME}` 和 `%NAME%`，环境变量必须已设置，配置文件中的字段名不会自动成为环境变量。
在实际运行的 Ubuntu 环境中生成配置，使用 `/data/research` 等 Linux 路径；WSL 2 中的用户目录和环境变量同样按 Ubuntu 解析。
数据、模型、缓存和运行输出路径必须在仓库外；生成的轻量配置文件可以留在 `.local/` 中。

| 字段 | 必填 | 默认派生位置或用途 |
| --- | --- | --- |
| `data_root` | 是 | 数据根目录 |
| `model_root` | 是 | 本地模型根目录；写入 Ψ₀ 环境的 `CVPR_MODEL_ROOT` |
| `run_root` | 是 | 运行与工具缓存根目录 |
| `archive_root` | 否 | `data_root/MixEgoMotion/smplh-parameters-v4-camera-quality` |
| `stats_path` | 否 | `data_root/MixEgoMotion/statistics/smplh_k12_5hz_joint_camera-quality-v4.pt` |
| `vision_profile_root` | 否 | `archive_root/vision_profiles/psi0_256x480_v1_30hz` |
| `window_cache_root` | 否 | `data_root/MixEgoMotion/training_cache/smplh245_5hz_w11_camera-quality-v4` |
| `motion_output_dir` | 否 | `run_root/motion/smplh_k12_psi0_256x480_5hz_camera_quality_v4_meanpool_from_scratch` |
| `dino_checkpoint` | 否 | 已存在的本地 DINO 模型目录；省略时使用固定 revision 的官方模型 |

`SPLIT_MANIFEST` 随 `archive_root` 定位为 `meta/splits.json`。若归档、统计或缓存分别存放，显式填写对应字段。
`dino_checkpoint` 必须指向真实存在的目录；生成器只检查目录存在，不把目录存在当作权重身份或模型兼容性验收。
省略该字段时不会根据 `model_root` 拼出一个假定存在的模型目录，DINO 配置保持官方示例中的固定模型 revision。

## 生成文件与使用边界

| 文件 | 用途 |
| --- | --- |
| `motion.local.json` | Motion 的本机配方；JSON 也是有效 YAML，可直接传给现有 `--config` 参数 |
| `dino.local.json` | 原生 30Hz DINO 提取配置；默认保留官方模型名、revision 和预处理参数 |
| `psi.local.env` | Ψ₀ 的 dotenv 路径项；不包含 token 或其它凭据 |
| `paths.resolved.json` | 解析后的路径和两份源配方 SHA256，方便核对来源 |

例如，在数据和 GPU 就绪验收完成后，原有训练入口可显式使用生成配置：

```bash
python -m MotionExpert.train --config .local/configs/motion.local.json --from-scratch
```

生成配方保留原正式实验的八卡、每卡 batch256 等参数；机器容量不同的用户应显式选择合适的已有 CLI 参数，并将最终实验配置记录下来。
完整训练、联合训练与评估步骤见[复现入口](../docs/reproduction/README.md)。

现有 Motion 读取器的归档优先级仍为 `--data-dir`、`MOTIONEXPERT_DATA_DIR`、配置文件。
使用生成配置前，应清除旧机器继承的 `MOTIONEXPERT_DATA_DIR`，或确保它与生成配置的归档相同；
该环境变量只覆盖归档及划分，不能同时迁移统计和各类缓存。

`psi.local.env` 包含 `CVPR_DATA_ROOT`、`CVPR_MODEL_ROOT`、`CVPR_RUN_ROOT`、`PSI_HOME`、`DATA_HOME`、`HF_HOME`、`TORCH_HOME`、`UV_CACHE_DIR`、`HF_LEROBOT_HOME`。
其中 Ψ₀ 目录位于 `run_root/psi`，工具缓存位于 `run_root/cache`。请将所需路径项合并到启动器读取的本地 `.env` 中，并保留自己的凭据与其它设置。
这是为 python-dotenv 编码的文件，不应当作 shell 脚本 `source`。UnifoLM 的 shell 环境示例单独见 [unifolm.env.example.sh](machines/unifolm.env.example.sh)。

本工具保留现有核心源码和旧配方，已有命令可以继续显式使用它们。
原始配方中的历史机器路径、实验收据、缓存身份和 GPU 验收不会被批量重写；迁移数据后仍需按各模块要求核对来源与就绪状态。
路径预览或配置生成成功，只说明路径配置可解析。
