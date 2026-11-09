# 文档导航

按使用目的选择入口。新环境先阅读安装和路径配置，再查看模块命令；带日期的实验、验收和交接材料保留各自的来源与适用范围。

## 使用与开发

| 目的 | 入口 |
| --- | --- |
| 环境安装与模块依赖 | [安装说明](setup/README.md) |
| 设置本机数据、权重和输出目录 | [路径配置](../configs/README.md) |
| 数据准备、训练、评估与推理 | [复现入口](reproduction/README.md) |
| 时间、坐标、张量与图像策略约定 | [数据与模型协议](protocols/README.md) |
| 固定上游、本地扩展和可选资源边界 | [第三方依赖说明](dependencies/README.md) |
| MotionExpert 接口与训练参数 | [MotionExpert](../MotionExpert/README.md) |
| 共享图像处理接口 | [ImageProcess](../ImageProcess/README.md) |
| 原生 30Hz DINO 特征提取 | [pipeline](../pipeline/README.md) |
| 双来源动作专家与 Ψ₀ 工程 | [VLMExpert](../VLMExpert/README.md) |
| 仿真、遥操作与本机工具 | [SIMPLE 工具](../scripts/4090_simple/README.md) |

## 已有实验与历史材料

- [实验记录索引](experiments/README.md)：按训练、数据、物理评估、遥操作和故障恢复分类，链接原文件。
- [整理前的完整首页](archive/README-2026-11-09.md)：保留原首页的协议描述、实验数字与状态语境。
- [整理前的代理协议快照](archive/AGENTS-protocol-2026-11-09.md)：保留旧任务的原始路径、状态和授权语境。
- [原环境与数据迁移说明](MIGRATION.md)：保留历史迁移流程和 Ψ₀ 展开依赖约定；新环境入口为上表的安装与路径配置。
- [Ψ₀ 来源清单](psi0_upstream.json)：固定上游提交、展开依赖与本地修改记录。
- [初次迁移文件清单](inventory/summary.json)：2026-10-06 的历史 inventory，不用于判断当前文件或训练协议。

实验记录中的机器绝对路径、PID、外部状态文件和“当前”描述属于记录时的上下文。复现时使用本机配置，核对对应数据、模型、代码版本和验收收据；避免把某次诊断、短时 GPU 检查或运行完成解释成全量任务验收。
