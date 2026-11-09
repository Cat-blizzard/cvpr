# 路径配置

配置工具生成 Motion、DINO 和 Ψ₀ 使用的数据、模型及输出路径。

## 使用方法

复制 [JSON 示例](machines/local.example.json)，填写自己的目录，然后生成配置：

```bash
mkdir -p .local
cp configs/machines/local.example.json .local/machine.json
# 编辑 .local/machine.json
python scripts/configure_paths.py --machine .local/machine.json
```

工具需要 PyYAML。默认目录为 `~/cvpr-data`、`~/cvpr-models` 和 `~/cvpr-runs`。
生成文件保存在 `.local/configs/`，通过 `--output-dir` 可更改位置。
`--dry-run` 预览路径；`--force` 覆盖已有配置。

## 配置字段

相对路径以 JSON 文件所在目录为基准。路径支持 `~`、`$NAME` 和 `${NAME}`；引用的环境变量需要已设置。
数据、模型、缓存和运行输出目录放在仓库外，配置文件可以保存在 `.local/`。

| 字段 | 必填 | 默认位置或用途 |
| --- | --- | --- |
| `data_root` | 是 | 数据根目录 |
| `model_root` | 是 | 模型根目录 |
| `run_root` | 是 | 运行输出和工具缓存根目录 |
| `archive_root` | 否 | `data_root/MixEgoMotion/smplh-parameters-v4-camera-quality` |
| `stats_path` | 否 | `data_root/MixEgoMotion/statistics/smplh_k12_5hz_joint_camera-quality-v4.pt` |
| `vision_profile_root` | 否 | `archive_root/vision_profiles/psi0_256x480_v1_30hz` |
| `window_cache_root` | 否 | `data_root/MixEgoMotion/training_cache/smplh245_5hz_w11_camera-quality-v4` |
| `motion_output_dir` | 否 | `run_root/motion/smplh_k12_psi0_256x480_5hz_camera_quality_v4_meanpool_from_scratch` |
| `dino_checkpoint` | 否 | 本地 DINO 模型目录；省略时使用固定版本的官方模型 |

数据分割文件随 `archive_root` 定位到 `meta/splits.json`。

## 生成文件

| 文件 | 用途 |
| --- | --- |
| `motion.local.json` | MotionExpert 的 `--config` 参数 |
| `dino.local.json` | DINO 提取器的 `--config` 参数 |
| `psi.local.env` | Ψ₀ 的 dotenv 路径变量 |
| `paths.resolved.json` | 解析后的完整路径 |

生成的 Motion 配置沿用原训练配方，默认使用 8 个 GPU、每卡 batch256；训练时可通过 `--devices` 和 `--batch-size` 覆盖。
Motion 的归档路径优先级为 `--data-dir`、`MOTIONEXPERT_DATA_DIR`、配置文件；使用生成配置时保持这些设置一致。

将 `psi.local.env` 中的变量合并到 `VLMExpert/.env`。UnifoLM 联合训练使用 [Bash 环境示例](machines/unifolm.env.example.sh)。
训练与评估命令见[使用指南](../docs/reproduction/README.md)。
