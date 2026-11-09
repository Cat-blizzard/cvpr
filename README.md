# Σ₀: From Human Interaction and Motion to Humanoid Loco-Manipulation

## Abstract

Humanoid loco-manipulation requires a robot to preserve a hand-object interaction while adapting its whole-body motion across varying initial states. Collecting synchronized whole-body teleoperation demonstrations is costly, yet egocentric videos offer scalable supervision at different action granularities: fine-grained wrist and fingertip trajectories capture object interaction, whereas sparse skeletal motion describes whole-body coordination. This supervision--execution asymmetry motivates learning the two priors separately and coupling them during robot control. We present Σ₀, a vision-language-action framework that learns an interaction prior through hand-action prediction and a coordination prior by jointly reconstructing observed skeletal motion and forecasting its future evolution. During robot-supervised post-training, the policy integrates both priors through proprioception-conditioned serial cross-attention, directly predicting robot-native body and hand actions without retargeting human motion. Across six SIMPLE tasks, Σ₀ achieves 92.8% success, surpassing the strongest baseline by 8.1 percentage points. With 10 demonstrations per task, Σ₀ achieves 83.3% success, whereas the variant without human-prior pretraining achieves 75.0% with 100 demonstrations per task. These results support data-efficient humanoid control from complementary human priors.

## 代码概览

面向第一视角运动预测与全身动作学习的研究代码，包含 MotionExpert、共享图像处理、DINO 特征提取，以及在固定 Ψ₀ 上游快照上加入的双来源 Action Expert。

运行平台以 **Ubuntu 22.04 LTS** 为目标，命令示例使用 Bash。WSL 2 中的 Ubuntu 可用于路径配置和 CPU 离线检查；GPU 训练与仿真仍按各自环境和资源完成验收。

MotionExpert 在 5Hz 上读取历史 5 帧与当前帧，联合重建历史运动并预测未来 5 帧；完整 11 个 motion hidden 可供下游使用并参与反向传播。VLMExpert 的 `dual_source_v1` 将 VLM tokens 与 motion hidden 接入动作专家。输入、坐标、视觉尺寸和缓存身份约定见 [数据与模型协议](docs/protocols/README.md)。

## 从这里开始

1. [安装与环境](docs/setup/README.md)：按特征提取、运动训练、VLM 或仿真用途准备独立环境。
2. [配置本机路径](configs/README.md)：设置数据、模型和运行输出目录，生成本机配置。
3. [复现入口](docs/reproduction/README.md)：按数据准备、训练、评估与推理顺序选择命令。
4. [模块文档](#模块)：查看接口和完整参数；已有实验的结果与边界见 [实验记录索引](docs/experiments/README.md)。

路径配置工具可先预览，不会启动训练或下载资源：

```bash
python scripts/configure_paths.py --machine configs/machines/local.example.json --dry-run
```

机器配置使用可编辑的 data/model/run 根目录。数据、权重、特征缓存、checkpoint 和运行环境存放在仓库外；生成的本机配置置于 Git 忽略的 `.local/configs/`。生成配置后仍需准备真实资源并满足原有验收条件，详见 [路径配置](configs/README.md)。

## 模块

| 模块 | 职责 | 文档 |
| --- | --- | --- |
| MotionExpert | 运动表示、训练、采样、数据读取与一步 hidden 接口 | [接口与训练](MotionExpert/README.md) |
| ImageProcess | 共享 RGB 几何、窗口同步增强与显式分支颜色策略 | [配置与接口](ImageProcess/README.md) |
| pipeline | 从已验收 SMPL-H 归档及原始相机视频提取原生 30Hz DINO | [格式与命令](pipeline/README.md) |
| VLMExpert | Ψ₀ 上游工程及本仓库的双来源动作专家、联合训练扩展 | [本地扩展与上游说明](VLMExpert/README.md) |

四个模块保留各自的安装边界。Motion、DINO、VLM 和仿真有不同依赖要求，具体版本与环境组合见 [安装说明](docs/setup/README.md)。源码路径还参与缓存与训练验收身份校验，整理文档和入口不会替换已有验收记录。

## 第三方代码与资源

VLMExpert 基于 Ψ₀ 的固定提交，并包含本地模型、数据和训练修改；其仿真、遥操作和其他 baseline 依赖按用途分别准备。[第三方边界说明](docs/dependencies/README.md) 列出上游来源和使用约定，[上游清单](docs/psi0_upstream.json) 保留固定版本及排除资源记录。各第三方目录沿用原许可与版权。

## 文档与实验记录

[文档总览](docs/README.md) 区分使用说明、协议、复现入口和实验记录。原首页中的训练进度、故障恢复及机器交接内容完整保存在 [2026-11-09 首页快照](docs/archive/README-2026-11-09.md)；这些记录具有各自的时间和验收范围，不代表当前运行状态。
