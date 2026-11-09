# 代码来源与依赖边界

本项目由独立模块、本地扩展的 Ψ₀ 工程和固定版本的仿真／控制依赖组成。安装按用途选择；源码快照、环境准备和资源验收分别管理。

## 核心模块与本地扩展

| 路径 | 当前职责与管理方式 |
| --- | --- |
| `MotionExpert/` | 运动模型、训练、窗口缓存与质量协议；独立安装 |
| `ImageProcess/` | Motion／DINO／VLM 共用的 RGB 几何和增强；轻量独立包 |
| `pipeline/` | 原始相机到原生 30Hz DINO 的提取包 |
| `VLMExpert/src/psi/` | 固定 Ψ₀ 快照上的本地 fork，包含双来源模型、训练和历史数据读取扩展 |
| `scripts/4090_simple/` | 本项目已有的本机资源、训练、仿真评估和采集工具；历史目录名保持兼容 |

Ψ₀ 来源为 [physical-superintelligence-lab/Psi0](https://github.com/physical-superintelligence-lab/Psi0)，初始快照固定在 `cda3fdfafe47cb6fa75400d013de1bd36e3cea05`。完整来源、排除文件及本地扩展清单见 [psi0_upstream.json](../psi0_upstream.json)。其中初始源码一致性与验收计数只描述导入时状态，后续改动以 Git 历史和对应验证报告为准。

本地扩展分布在 `models/`、`config/`、`trainers/`、`data/` 等目录，包括 masked mean pooling、`dual_source_v1`、MotionExpert 联合训练和 UnifoLM DINO 历史读取。更新 Ψ₀ 时需比较这些差异并保留接口协议。

`VLMExpert/src/` 中还包含其他基线源码，使用入口见 [baselines](../../VLMExpert/baselines/README.md)。它们按自身依赖准备环境；阅读和使用本地双来源模型不要求同时安装所有基线。

## 展开的第三方快照

| 路径 | 固定提交 | 用途 |
| --- | --- | --- |
| `VLMExpert/third_party/GR00T-WholeBodyControl` | `d40376994ff094787591ab76a691c50b8e131786` | 全身控制、SONIC 及相关部署资源 |
| `VLMExpert/third_party/SIMPLE` | `803db7e4c1f0fef11008c9480ee75b2f9cc0ca36` | 仿真、任务、机器人及控制适配 |

SIMPLE 内还展开 AMO、XRoboToolkit、cuRobo、decoupled_wbc、gear_sonic、gsnet、openpi-client 和 unitree_sdk2_python。各自来源和精确提交由 [快照清单](../psi0_upstream.json) 记录；本轮整理保持原目录和版本。

这些目录是普通跟踪文件，当前索引没有对应 gitlink。保留的 `.gitmodules` 记录上游来源；本仓库的依赖准备不使用 `git submodule update --init --recursive`。不要根据其上游分支名直接替换固定快照。

训练所需 LeRobot 为 `songlin/lerobot@09929d8057b044b53aecaf5c6d7eb71f99e8beb9`，通过 [VLMExpert/pyproject.toml](../../VLMExpert/pyproject.toml) 与锁文件约束；它与展开源码目录采用不同的安装机制。

## 许可与外部资源

各依赖原目录中的许可、版权和资源声明继续保留。例如 [Ψ₀ LICENSE](../../VLMExpert/LICENSE)、[GR00T LICENSE](../../VLMExpert/third_party/GR00T-WholeBodyControl/LICENSE)、[cuRobo LICENSE](../../VLMExpert/third_party/SIMPLE/third_party/curobo/LICENSE) 与 [资产许可](../../VLMExpert/third_party/SIMPLE/third_party/curobo/LICENSE_ASSETS)。代码许可与模型、数据及机器人资源许可分别遵循各自来源要求。

Git LFS 由根 `.gitattributes` 管理。网格、SDK 库和归一化统计可能是已保留的运行依赖；权重、训练数据、环境、日志和其他未分发的仿真资产按来源清单另行准备。完整排除项见 `excluded_upstream_paths`，本机资源检查见 [环境工具](../../scripts/4090_simple/README.md)。

机器绝对路径只用于本机配置和历史证据。新机器从 [安装指南](../setup/README.md) 生成自己的路径配置，所需来源身份与验收规则继续有效。
