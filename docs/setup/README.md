# 安装与本机路径

运行平台以 Ubuntu 22.04 LTS 为目标，下列命令使用 Bash，从仓库根目录执行。数据、权重、运行环境、训练输出和资源缓存放在仓库外；本机配置保存在忽略跟踪的 `.local/`。

## 先生成本机配置

路径配置工具只需要 Python 3.10+ 和 PyYAML，不需要 Torch、CUDA 或数据集。以下示例使用当前已激活的 Python 环境；需要隔离时，在仓库外建立专用环境。

全新 Ubuntu 22.04 若尚无可用的 Python 环境，可先为配置工具创建轻量环境：

```bash
sudo apt-get update
sudo apt-get install python3.10-venv
python3.10 -m venv "$HOME/.venvs/cvpr-tools"
source "$HOME/.venvs/cvpr-tools/bin/activate"
```

这一步只准备配置工具环境；后续模型和仿真仍使用下文各自的环境。

Ubuntu / Bash：

```bash
python -m pip install PyYAML
mkdir -p .local
cp configs/machines/local.example.json .local/machine.json
# 编辑 .local/machine.json，选择本机数据、模型和输出根目录。
python scripts/configure_paths.py --machine .local/machine.json --dry-run
python scripts/configure_paths.py --machine .local/machine.json
```

默认根目录为当前用户的 `~/cvpr-data`、`~/cvpr-models`、`~/cvpr-runs`。根目录及归档、统计、视觉缓存等具体路径都可覆盖；相对路径以机器配置文件所在目录为基准，含空格的路径在命令行中加引号。完整字段和覆盖规则见 [配置说明](../../configs/README.md)。

生成文件位于 `.local/configs/`：

| 文件 | 用途 |
| --- | --- |
| `motion.local.json` | 交给 MotionExpert 的 `--config`；JSON 可由现有 YAML 读取器加载 |
| `dino.local.json` | 交给特征提取入口的 `--config`；默认使用固定 revision 的官方 DINO |
| `psi.local.env` | Ψ₀ 的本机路径变量，采用 dotenv 格式 |
| `paths.resolved.json` | 检查实际解析出的本机路径 |

工具默认拒绝覆盖已有文件，重新生成时先比较配置，再按需使用 `--force`。`--dry-run` 不写文件。生成配置不下载资源，也不授予数据、缓存或模型验收。

`psi.local.env` 供 dotenv 读取，不是 Bash 脚本。首次配置 Ψ₀ 时，可把其中需要的路径项合并到 `VLMExpert/.env`；保留已有凭据和项目设置。路径文件应在实际运行的 Ubuntu 环境中生成，使用该环境中的 Linux 路径。

## 按用途安装环境

| 用途 | 环境边界 | 依赖依据 |
| --- | --- | --- |
| 图像处理 | Python ≥3.10；NumPy、Pillow | [ImageProcess](../../ImageProcess/pyproject.toml) |
| MotionExpert 训练／推理 | Python ≥3.10；匹配驱动的 Torch，再安装模块依赖 | [MotionExpert](../../MotionExpert/pyproject.toml)、[requirements](../../MotionExpert/requirements.txt) |
| DINO 特征提取 | 独立 Python ≥3.10 环境，安装 `pipeline[dino]` | [pipeline](../../pipeline/pyproject.toml) |
| Ψ₀／双来源模型 | 独立 Python 3.11；Torch 2.7.0、Transformers 4.57.1 及固定 LeRobot | [VLMExpert](../../VLMExpert/pyproject.toml)、[uv.lock](../../VLMExpert/uv.lock) |
| SIMPLE 仿真与控制 | 专用 Python 3.10；与 Python 3.11 模型服务分开 | [仿真环境指南](../../scripts/4090_simple/README.md#conda-与依赖) |

在相应的独立环境中，先安装匹配本机 CUDA／驱动的 PyTorch，再从仓库根目录安装对应模块：

```bash
# MotionExpert 环境
python -m pip install -e ./ImageProcess
python -m pip install -e ./MotionExpert

# 切换到 DINO 提取环境后
python -m pip install -e ./ImageProcess
python -m pip install -e "./pipeline[dino]"
```

这些模块依赖给出可安装范围；新机器应记录实际安装版本，不把它们当作完整环境锁文件。图像处理身份包含 NumPy／Pillow 版本，读取既有视觉缓存时仍需匹配其协议。

Ψ₀ 的独立安装命令见 [迁移说明](../MIGRATION.md#独立安装)。在它的专用环境中同时安装本地 `ImageProcess`、`MotionExpert`，需要特征提取时再安装 `pipeline[dino]`。FlashAttention 等扩展须匹配 Python、Torch、CUDA 与 C++ ABI；仿真侧另按现有约束文件安装。

## WSL 2 中的 Ubuntu

本机已确认 WSL 2 的 Ubuntu 22.04.5 LTS 可正常启动，系统 Python 为 3.10.12。可在该 Ubuntu 环境中检查本机路径配置和 CPU 离线测试；生成的用户目录、环境变量和资源路径均以 Ubuntu 环境为准。

本次检查的命令和结果见 [Ubuntu 离线验证记录](../experiments/ubuntu-validation-2026-11-09.md)。

完整 CUDA 训练、Isaac Sim、SIMPLE 与真机运行仍需各自的依赖和资源验收。WSL 2 能启动、路径生成成功或离线测试通过，只覆盖对应检查范围。

## 下一步

按 [复现入口](../reproduction/README.md) 准备数据和选择任务；方法及输入输出约定见 [协议索引](../protocols/README.md)。已有机器上的训练记录、资源交接和历史绝对路径见 [实验记录](../experiments/README.md)。
