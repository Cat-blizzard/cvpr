# Ubuntu 离线验证（2026-11-09）

本次验证针对本机路径配置、下载器与监控工具。运行于现有 WSL 2 的 Ubuntu 22.04.5 LTS，
Python 为系统 `/usr/bin/python3`（3.10.12），内核为 `5.10.102.1-microsoft-standard-WSL2`。
仓库通过 `/mnt/d/CVPR` 挂载；测试临时数据写入 Linux `/tmp` 并清理。

## 检查结果

| 检查 | 结果 |
| --- | --- |
| 本机路径生成工具 | 9 项通过，1 项 dotenv 解析检查因缺少 `python-dotenv` 跳过 |
| EgoExo-4D HM 下载器离线测试 | 24 项通过 |
| EgoExo-4D HM 监控器离线测试 | 10 项通过 |
| EgoSuite 监控器离线测试 | 7 项通过 |

合计 50 项通过、1 项跳过；未进行真实数据下载。命令在仓库根目录执行：

```bash
python3 -B -m unittest discover -s scripts/tests -p test_configure_paths.py -v
python3 -B -m unittest discover -s datasets -p test_download_egoexo4d_hm.py -v
python3 -B -m unittest discover -s datasets -p test_monitor_egoexo4d_hm.py -v
python3 -B -m unittest discover -s datasets -p test_monitor_egosuite.py -v
```

路径工具测试覆盖原配方非路径参数一致性、实际 Motion 配置读取、相对路径与环境变量、
覆盖保护、缺失模型错误，以及预览模式无写入。测试中的 BOM 和反斜杠输入是文件编码边界检查，
不代表项目提供 Windows 运行支持。

## 环境与验证范围

此 Ubuntu 已有 PyYAML、NumPy 和 Linux `fcntl`；未发现 Torch、mcap、pyarrow 或 python-dotenv。
因此未运行 EgoSuite 完整下载器、VLM、GPU 模型和物理仿真测试。
当前 PATH 和 `/usr/lib/wsl/lib/` 均未发现 `nvidia-smi`，本次没有验证 GPU 透传或 CUDA。

系统缺少创建带 pip 虚拟环境所需的 `ensurepip`；本次改用现有系统解释器进行上述离线检查，
没有安装系统包或改变现有 Python 环境。后续完整环境按[安装说明](../setup/README.md)独立准备。

这些结果仅确认本轮路径配置和所列离线工具在 Ubuntu 上的行为，不替代数据、缓存、权重身份、
GPU 训练或仿真验收。源码哈希绑定与原始验收证据保持原样。
