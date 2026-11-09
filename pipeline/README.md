# MixEgoMotion：当前数据与 DINO 提取

默认提取配置为 [`configs/dino.json`](configs/dino.json)，可按需编辑。路径说明见[项目首页](../README.md#configuration)。

## 数据格式

数据根目录通过[路径配置](../README.md#configuration)指定。

```text
MixEgoMotion/
├── smplh-parameters-v4-camera-quality/
│   ├── meta/                  # info、episode索引、train/val/test分割
│   ├── episodes/XXXXXXXX/
│   │   ├── motion.parquet     # 原生30Hz运动参数与显式标签
│   │   └── receipt.json       # 原始不可变提交凭证
│   ├── weights/smplh/         # 自有共同人体模型与手部表示资源
│   └── vision_profiles/psi0_256x480_v1_30hz/  # 原有DINO按相同字节复用
├── statistics/smplh_k12_5hz_joint_camera-quality-v4.pt         # 相机质量mask修订后的全量train统计
├── weights/dinov2-with-registers-large/     # 保留DINO预训练权重
└── training/                               # 新训练产物
```

`motion.parquet` 保留：

- `smplh.root_orient [3]`、`pose_body [63]`、`trans [3]`、`betas [16]`，以及来源可用时的手指PCA。
- 左右各21点世界XYZ及逐点mask，独立于手指PCA可用性。
- 相机／头部／头戴参考世界位置、四元数、mask及插值标记。
- v4受影响episode额外保存相机点质量与原生incoming-edge连续性mask；其余episode由独立全有效证书继承原mask。
- 地面高度、法向、有效性／认证标记，原始双脚点及mask。
- 身体估计与来源观测的独立位置／旋转mask、confidence、完成及残差信息。
- 原生frame/index、时间、视频帧号、PTS误差及原始图像mask。

共同模型定义SMPL-H身体22关节轴，世界坐标米、Z-up。MotionExpert构建窗口缓存时做FK并选既有K12，训练直接mmap读取，
同时构建相机地面参考坐标和接触代理；不在归档增加dense22缓存。
共同模型SHA256为 `be42bff1ff0589cf0467893bcfbbeb3f9b533ba151031c8cdfb64ca1dcb34947`。

## 图像与特征协议

共享配置位于 [ImageProcess](../ImageProcess/README.md)：

| 阶段 | 初始尺寸 H×W | 最终共享RGB H×W | 增强 |
| --- | --- | --- | --- |
| 预训练 | 270×480 | 256×480 | 确定性处理 |
| 后训练 | 240×320 | 256×320 | 窗口共享颜色增强 |
| Robust | 270×480 | 256×480 | 窗口共享颜色及随机裁切 |
| 验证／真机推理 | 按对应profile | 按对应profile | 确定性处理 |

表中后训练和Robust的窗口共享增强指通用在线 `shared_rgb` 模式。当前UnifoLM配方例外：
`vlm_color_clean_motion` 只增强VLM当前帧颜色，Motion历史六帧复用clean 256×320 DINO缓存；
两路保持同源、同时间、同几何profile，不启用随机裁切，现有缓存无需重提取。
详见 [ImageProcess的分支增强说明](../ImageProcess/README.md#unifolm-vlm-color-clean-motion-history)。

DINO为冻结的 `dinov2-with-registers-large`。共享RGB处理后关闭HF的二次resize/crop，
只执行DINO自身归一化，输出 `[5,1024] float32`，顺序CLS、register0..3。
原始MCAP／MP4保持来源相机既有几何约定；共享模块不新增去畸变。

离线特征保存全部原生30Hz帧。MotionExpert按索引0、6、12…取5Hz，
每窗口11帧，前6帧为历史5帧＋当前帧，后5帧为未来。
特征只允许历史6帧作为条件，未来隐藏。

新缓存格式：

```text
vision_profiles/psi0_256x480_v1_30hz/
├── manifest.json
└── episodes/XXXXXXXX/
    ├── features.npy          # [T30,5,1024]，float32，支持mmap
    ├── join.npz              # 原生帧号／时间／来源视频帧号／PTS／mask
    └── receipt.json          # 来源record、encoder/profile、输出文件身份
```

提取恢复只复用同配置、同来源、同文件身份的已完成episode。
坏帧不提升为有效，输出mask必须与原始来源mask相同，否则正式提取或训练拒绝。
训练要求完整 `complete/all` manifest与同一归档、分割、图像profile绑定。
视觉尺寸变化本身不要求重算运动统计；相机质量mask变化时需要重新计算全train统计。视觉版本另行写入checkpoint。

## 全量提取命令

从仓库根目录执行。
```bash
python -m egomotion_pipeline.cli extract-smplh-features \
  --dataset "<ARCHIVE_ROOT>" \
  --output "<VISION_ROOT>" \
  --config pipeline/configs/dino.json \
  --gpus 0 \
  --workers-per-gpu 1
```

同命令再次执行可以恢复。加 `--dry-run` 只检查原始视频来源与提取计划，不加载DINO、不创建输出。
`--episodes` 只用于独立诊断目录，部分缓存不能用于正式训练。
MotionExpert从头训练命令见 [MotionExpert README](../MotionExpert/README.md)。

后训练／Robust用 `DinoEncoder.encode_window(history_rgb, stage=..., seed=...)` 在线编码，
将返回的 `rgb[-1]` 同时送入Ψ₀，确保当前帧与增强完全相同。
增强变化后不能复用固定离线embedding。运动时间、坐标、标签和mask保持原协议。
