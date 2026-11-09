# MotionExpert

路径配置见[配置说明](../README.md#configuration)，训练与评估入口见[使用说明](../README.md#training)。以下命令从仓库根目录执行。

在5Hz上读取历史5帧＋当前帧图像，联合重建历史运动并预测未来5帧。当前帧与Ψ₀当前帧同源、同时间。
后训练在完整高斯噪声 `t=1` 上执行一次网络调用，得到完整11个motion hidden供下游输入，同时提供mean pooling摘要；
该接口保留反传能力，下游模型不在本模块内。**没有可学习GLOBAL token。**

## 时间、图像与条件

11个时刻为 `[-1,-0.8,-0.6,-0.4,-0.2,0,0.2,0.4,0.6,0.8,1]` 秒。
原始运动和离线DINO均为30Hz，MotionExpert按零相位、步长6取5Hz。
输入DINO为 `[B,6,5,1024]`，每帧CLS＋4 register。未来5帧图像不作为条件。
模型联合监督11帧运动，不输入干净历史人体姿态。

| 阶段 | 最终RGB H×W | 增强 |
| --- | --- | --- |
| 预训练 | 256×480 | 确定性共享几何 |
| 后训练 | 256×320 | 窗口共享颜色增强 |
| Robust | 256×480 | 窗口共享颜色＋随机裁切 |

表中后训练和Robust的窗口共享增强指通用在线 `shared_rgb` 模式：两路复用同一处理后的当前RGB，
各自归一化，并在线编码冻结DINO。共享处理见 [ImageProcess](../ImageProcess/README.md)。
当前UnifoLM配方显式使用 `vlm_color_clean_motion`：只增强VLM当前帧颜色，Motion历史六帧复用
clean 256×320 DINO缓存；两路保持同源、同时间、同几何profile，不启用随机裁切。
具体策略见 [VLMExpert](../VLMExpert/README.md#本仓库扩展双来源-action-expert)。
真机先攒满约1秒历史再启用运动先验；接口要求6个真实时刻，不复制首帧补历史。

训练保留历史轨迹模态dropout：每样本概率0.5开放前6帧有效18维相机轨迹。
验证、测试和 `forward_features()` 隐藏真实轨迹；未来图像和轨迹始终隐藏。
身体和手部真值及其有效mask只参与监督。`t=1` 的全部245维是完整高斯噪声，缺失标签不能把噪声清零。

## 运动表示

归档保存共同SMPL-H模型的参数；reader做FK后选择K12：
`[0,4,5,10,11,13,14,15,18,19,20,21]`，对应pelvis、左右knee、左右foot、
左右collar、head、左右elbow、左右wrist。双手使用左右各21点显式XYZ监督。
表示版本 `smplh12_rot6d_hands21_contacts_v1`，身体轴为 `smplh_body22_axes_v1`。

| 通道切片 | 内容 | 维数 |
| --- | --- | ---: |
| `[0:108]` | 身体12关节，逐关节旋转6D＋XYZ | 108 |
| `[108:117]` | 相机地面参考系旋转6D＋平移3D增量 | 9 |
| `[117:180]` | 左手21点XYZ | 63 |
| `[180:243]` | 右手21点XYZ | 63 |
| `[243:245]` | 双脚接触代理 | 2 |
| 总计 | 运动输入／输出 | **245** |

另有18维轨迹：相机相对地面参考位姿9维＋参考运动增量9维。重复增量共享统计。
6D取旋转矩阵前两行；世界坐标米、Z-up。窗口首帧相机水平位置／朝向规范化，逐帧使用相机地面参考系。
相邻增量在上一帧参考系表达，首帧保留初始参考约定。模型不预测完整SMPL-H pose或shape。
地面优先使用有效归档值，缺失时只用历史6帧有效原始脚点平均高度减2cm兜底。
接触按5Hz重算，速度0.2m/s、高度0.1m，为代理标签。

## 当前数据与相机质量修订

数据根目录由路径配置指定，所需文件包括：

| 产物 | 相对路径 |
| --- | --- |
| 运动归档 | `smplh-parameters-v4-camera-quality` |
| 原分割 | `smplh-parameters-v4-camera-quality/meta/splits.json` |
| DINO | `smplh-parameters-v4-camera-quality/vision_profiles/psi0_256x480_v1_30hz` |
| 窗口mmap | `training_cache/smplh245_5hz_w11_camera-quality-v4` |
| 全train统计 | `statistics/smplh_k12_5hz_joint_camera-quality-v4.pt` |

HM从原始Aria closed/open-loop读取逐时刻质量、时间、graph/session及速度证据。
质量必须有限且大于0，**不把0.5统一判坏**；最近位姿误差不超过20ms。
时间匹配使用整数纳秒，等距选较晚位姿，与原Aria SDK实际CLOSEST行为一致。
所有中间源样本也必须连续，MPS间隔不超过20ms；graph/session变更或跟踪缺口禁止跨边。
closed-loop仍是原世界坐标位姿，open-loop只用于质量和连续性，不替换原位姿。
原生边位移超过 `0.10m＋3×源速度上界×Δt` 或转角超过 `0.20rad＋3×源角速上界×Δt` 时屏蔽该增量。
另设宽松物理边界15m/s、20rad/s。这些是保守工程门限，策略和拒绝原因随审计保存。
EgoSuite原MCAP相机消息没有confidence字段，不伪造置信度；检查实际schema、有限位姿、时间和刚体运动边界。

区分绝对点与相邻边：

- `observation.valid.camera_tracking`：原生相机点质量。
- `observation.valid.camera_transition[i]`：原生 `i-1→i` 的连续性；首帧采用点有效性。
- reader先检查5Hz两帧之间**全部30Hz点及边**，再生成18维轨迹及9维参考增量mask。
- 相机点失效，相关相机／头戴参考和局部监督随之失效；边失效只禁止跨边增量。
- 原始SMPL-H参数、world手／脚、原地面、RGB与DINO数值保留；独立观测不会因相机失败被删除。
- 首帧参考失效的窗口拒绝；不从未来挑选替代锚点。训练索引排除没有有效未来身体监督的窗口。

两列只在需要修订的episode新增，以保留其余Parquet的原始文件身份；未改变episode拥有独立的
原生参考全有效证书，reader按原camera/head-reference mask兼容读取，并统一输出窗口transition mask。

相机审计、修订构建、独立验收分别由 `audit_camera_quality`、`revise_camera_archive`、
`validate_camera_revision` 完成；候选写出不能自行授予独立验收。报告位于归档 `.pipeline/camera-quality/`。
这些原始来源审计使用可选依赖：在仓库根目录执行 `python -m pip install -e './MotionExpert[audit]'`。
普通训练无需安装该 extra。
归档发布与训练就绪分开：缓存、新全train统计、当前架构GPU验收完成前 `formal_training_ready=false`。
正式训练入口绑定统计SHA、窗口manifest、当前模型架构及GPU报告/实现身份，拒绝旧mask或过期验收。

### 固定窗口 mmap 缓存

预训练配置显式使用窗口缓存。原始float32 `[11,245]`、`[11,18]`、bool mask和解码变换
按episode生成，再按split打包为只读 `.npy`，省去训练时重复Parquet、FK和坐标计算。
普通窗口读取与批量缓存构建共用原生相机连续性计算；滑动窗口首帧保留初始参考约定，后续增量不能跨坏边。
缓存身份同时绑定读取器、表示和完整窗口生成器源码，防止生成逻辑改变后误用旧缓存。
噪声、条件dropout仍在训练时生成，DINO继续按episode mmap读取。
每个episode数组先读回比对RAM结果，打包后检查完整payload和冻结索引；独立验收再比较代表来源窗口。

`reuse_window_cache --camera-quality-reuse` 只允许review固定的完整新旧源码哈希对、
已发布的父子独立验收，以及逐episode全部原生参考／边有效的证书。
只有完整record和原始文件身份都一致的episode才能复用；其余重建，不复制旧acceptance。
普通构建可恢复已提交shard，最多8worker。原生质量mask变化后必须重新统计完整train，不能复用v3统计。

```bash
MOTION_PY=python
CONFIG=.local/configs/motion.local.json
CACHE="<WINDOW_CACHE_ROOT>"
RAW_CACHE_REPORT="<RAW_CACHE_REPORT>"
NORMALIZED_CACHE_REPORT="<NORMALIZED_CACHE_REPORT>"

"$MOTION_PY" -m MotionExpert.build_window_cache --config "$CONFIG" --output-root "$CACHE" --workers 8
"$MOTION_PY" -m MotionExpert.validate_window_cache --config "$CONFIG" --source-config "$CONFIG" \
  --raw-only --report "$RAW_CACHE_REPORT"
"$MOTION_PY" -m MotionExpert.compute_cached_motion_stats --config "$CONFIG" \
  --archive-root "<ARCHIVE_ROOT>" \
  --cache-root "$CACHE" --acceptance "$RAW_CACHE_REPORT" \
  --output "<STATS_PATH>"
"$MOTION_PY" -m MotionExpert.validate_window_cache --config "$CONFIG" --source-config "$CONFIG" \
  --gpu-check --device cuda:0 --report "$NORMALIZED_CACHE_REPORT"
```

`RAW_CACHE_REPORT`、`NORMALIZED_CACHE_REPORT` 必须设置为仓库外本次job报告路径。
统计输出拒绝覆盖已有文件；raw报告不能代替训练所需的归一化/GPU验收。
新统计内嵌 `window_cache_provenance`，绑定产生它的缓存manifest与原始接受报告字节身份；
v4训练入口及归一化缓存Dataset核对这条绑定，同一v4归档下重新生成的缓存也不能搭配旧统计。
旧缓存自动切换工具只适合同一架构、相同统计的完整续训。

## 模型、归一化与异常保护

架构版本为 `e7_smplh12_hands21_meanpool_qkvnorm_v2`。
仅保留一个flow-time prefix，不参与global pooling；全部11个motion token参与均值，不按监督mask加权。
self-attention Q/K/V共用归一化后的motion；cross-attention的Q使用自身LayerNorm，
K/V对图像和时间context单独做不带仿射参数的LayerNorm。
旧GLOBAL／旧注意力checkpoint不能直接resume、init或warm-start到本架构。

保护在反向传播前检查非有限预测、实际加权loss、逐样本加权flow loss和每层每token RMS最大值，
优化器更新前检查**unscale后、clip前**的梯度。DDP先汇总再一致停止，避免一张卡退出、其他卡继续反传。

| 配置 | 默认值 |
| --- | ---: |
| `SAFETY_MAX_LOSS` | 100 |
| `SAFETY_MAX_GRAD_NORM` | 1000 |
| `SAFETY_MAX_ACTIVATION_RMS` | 100 |
| `SAFETY_ROLLING_WINDOW` | 128 |
| `SAFETY_ROLLING_WARMUP_STEPS` | 32 |
| `SAFETY_ROLLING_MULTIPLIER` | 50 |
| `SAFETY_ROLLING_MIN_LOSS` | 1 |

loss绝对上限从第一步生效，只约束 `loss`、`flow_loss`、`per_sample_flow_loss`；
所有未加权分组MSE与辅助诊断仍检查NaN/Inf并记录最大值，不共用实际优化目标的幅值门限。
32个健康训练批次后，batch loss还须不超过 `max(1, 50×健康历史中位数)`。
这些是可配置保护上限，不代表最佳训练超参。关闭幅值保护仍拒绝NaN/Inf。
FP16＋fused AdamW因不能保证pre-step时已unscale而拒绝；当前BF16＋普通AdamW可用。
异常时在 `TRAIN.EXP_PATH/anomalies/` 保存各卡batch、mask、来源、RNG、实际x_t/t、条件及参数身份，
保留参与梯度累积的microbatch，不进行该次参数更新，不写大型checkpoint。
诊断包不包含当时完整权重，单独一个batch文件不能重现整个模型状态。
正常步不写诊断文件；额外记录 `train/unclipped_grad_norm`、`train/activation_rms_max`。

## 训练配置与手动命令

| 参数 | 设置 |
| --- | --- |
| GPU／batch／workers | 8卡，每卡256，全局2048；每卡24workers |
| 优化器 | AdamW，LR1e-4，weight decay0.01，梯度裁剪1.0 |
| 精度 | BF16 mixed |
| 周期 | 200 epochs；正式配置显式设置10轮warmup，然后cosine至1e-5 |
| 保存／验证 | 每20轮保存，结束保存final；每5轮验证 |
| 模型 | hidden768、12层、1 shared＋11 routed experts、Top-2 |
| 生成 | x0 Flow Matching，10步Euler；EMA0.992028 |
| 跨卡通信 | 单机启用P2P／NVLink及共享内存；IB关闭，loopback用于连接建立及必要的回退 |
| 指标同步 | `BATCHED_METRIC_SYNC=true`；每10步合并同步，epoch均值保留全部训练样本 |
| 优化器融合 | `FUSED_ADAMW=false`，继续使用普通AdamW |

从头训练：

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
NCCL_IB_DISABLE=1 NCCL_P2P_DISABLE=0 NCCL_SHM_DISABLE=0 NCCL_SOCKET_IFNAME=lo \
python \
  -m MotionExpert.train --config .local/configs/motion.local.json --from-scratch
```

输出目录由配置中的 `TRAIN.EXP_PATH` 指定。
Lightning启动DDP，无需另套torchrun。后续同架构续训须使用同一统计与视觉身份。
从已有checkpoint续训：

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
NCCL_IB_DISABLE=1 NCCL_P2P_DISABLE=0 NCCL_SHM_DISABLE=0 NCCL_SOCKET_IFNAME=lo \
python \
  -m MotionExpert.train --config .local/configs/motion.local.json \
  --resume "<CHECKPOINT_100>" \
  --max-epochs 200
```

恢复优化器、EMA、调度和 step 计数，并继续原任务的学习率日程。

上述通信设置适用于当前单机八卡；显式覆盖继承的P2P／SHM禁用环境，正式命令不再使用
`--ddp-socket`。该选项仍保留为通信兼容性回退，会关闭P2P和共享内存。
启动设置允许P2P不代表一定采用，须结合NCCL日志中的 `via P2P/IPC` 验证实际传输路径。
合并指标只改变日志通信：`train/loss_step` 保留日志时刻的全局batch均值，
`train/loss_epoch` 按样本数汇总整轮，包含最后一个日志周期之后的尾批。
逐步loss／激活／梯度异常保护、梯度同步和动态空专家检查继续启用。

## 每轮更新loss曲线

`watch_loss.py` 独立读取TensorBoard日志，不加载模型、checkpoint或运动数据，不修改训练进程。
默认每完成1轮，更新从第1轮到当前已完成轮次的曲线；启动时先绘制已有完整历史。
训练曲线使用 `train/loss_epoch` 的真实整轮均值，验证曲线使用已有的 `val/loss`，
不把每10步记录的batch loss当作整轮均值。没有整轮记录的当前轮不会提前画入。

直接执行文件，避免导入训练包；绘图需要TensorBoard及可选依赖 `matplotlib>=3.7,<4`。
运行命令：

```bash
python -u MotionExpert/watch_loss.py --run-dir "<RUN_DIR>" \
  --every-epochs 1 --poll-seconds 30
```

默认从 `.pipeline/current_motionexpert_training.json` 解析训练目录，并在启动时绑定该任务。
输出位于训练目录的 `plots/`，数据及图片均不进入Git：

- `loss_curve.png`：每轮覆盖更新的完整历史曲线，轮数从1开始。
- `loss_history.csv`：每轮训练均值和已有验证值，保留缺失项。
- `status.json`：绘图进程、最近完成轮数、输出路径和更新时间。

用 `--run-dir /绝对路径` 可查看指定任务，`--output-dir` 可指定输出位置；
`--once` 只刷新一次后退出。相同输出目录仅允许一个绘图进程，停止绘图不影响训练。
日志晚写入的epoch或验证值会在后续扫描补上；不会将另一个训练任务混入当前曲线。

## 一步hidden与在线共享图像

`forward_features()` 保留autograd；默认没有CFG，单次 `t=1` 前向：

- `one_step_hidden [B,11,768]`：全部11个运动时刻的最后一层hidden。
- `one_step_global [B,768]`：严格等于 `one_step_hidden.mean(dim=1)`。

不运行完整10步采样，不输入干净人体目标，不使用未来标签mask。
seed可固定初始噪声；训练模式下dropout仍遵循调用方RNG。显式CFG会多一次无条件调用，合成hidden后再求均值。

```python
import json
import torch
from MotionExpert import MotionExpert
from egomotion_pipeline.features import DinoEncoder

expert = MotionExpert(weights="new-run/checkpoint.ckpt", device="cuda", dtype=torch.float32,
                      use_ema=False).train()
encoder = DinoEncoder(json.load(open(".local/configs/dino.local.json")))
# 5Hz六个真实时刻，最后一帧就是Ψ₀当前帧。
window = encoder.encode_window(history_rgb, stage="posttrain", seed=123)
img_embs = torch.from_numpy(window["img_embs"])[None].to("cuda")
features = expert.forward_features({"img_embs": img_embs}, seed=0)
prior = features["one_step_hidden"]  # [B,11,768]，保留所有时刻；不预先mean pooling
# Ψ₀使用window["rgb"][-1]；下游loss经prior反传更新运动网络。
```

Robust使用 `stage="robust"`；DINO始终冻结。外部nn.Module／DDP应把 `expert.model` 注册为子模块。
只用hidden时输出head不参与梯度，DDP需处理未使用参数，如 `find_unused_parameters=True`。
冻结特征用 `extract_features()`；完整预测用 `predict_future()`，返回未来 `[B,5,245]` 和完整 `[B,11,245]`。

## 冻结运动先验验证

`probe_prior` 比较第20轮、第100轮的 `t=1`、11个hidden均值与历史DINO基线。
MotionExpert全程EMA／FP32／eval／禁止梯度，只训练独立的线性ridge读出；不会恢复运动训练。
直接读取已验收train／val packed mmap及按需DINO，不扫描原始归档、解码Parquet或执行FK。

```bash
python -u \
  -m MotionExpert.probe_prior \
  --checkpoint20 "<CHECKPOINT_20>" \
  --checkpoint100 "<CHECKPOINT_100>" \
  --output "<PROBE_OUTPUT>" \
  --gpus 0,1,2,3,4,5,6,7
```

输出目录必须全新且位于仓库外。默认每来源train最多1024个episode、val最多256个，
每episode最多16窗，窗口起点相距至少60个原生帧；三组使用相同样本、标签及逐窗噪声。
输入仅历史6帧图像和历史图像有效性，不输入相机轨迹、真实运动或未来标签mask。

标签为当前帧固定相机地面系中的未来腕位移、参考XY位移与yaw，以及脚接触和相对当前接触状态变化。
腕使用显式hands21的第0点；相机参考链中任一坏边阻断依赖该链的位移标签。
接触监督保持独立。yaw以sin/cos拟合、环绕角误差评分。

DINO保留6×5×1024时序后仅在train拟合PCA768，记录解释方差；三个读出均为相同维度。
正则强度只在原train内部按人物／录制连通组选择，原val仅评分。
结果分EgoSuite／HM报告，包含episode宏平均、有效覆盖和按原连通组配对bootstrap区间。
接触读出采用线性最小二乘与0.5阈值，未经概率校准。

`plan.json`、`selection.json`、`gpu-check-*.json`、`metrics.json`、`report.md`、冻结特征及
小读出权重均保存于输出目录。附带256个val窗口的三份噪声特征，用于判断噪声敏感性。
`--stage extract` 仅提取；`--stage fit` 在已提取的同一输出目录拟合读出。
该验证衡量冻结pooled特征的运动信息可读性，不直接等同于下游注入收益；DINO压缩也可能丢失信息。

增加第160轮对照时，复用已有 probe 输出目录，保持原窗口顺序、标签、DINO和逐窗噪声：

```bash
python -u \
  -m MotionExpert.probe_prior \
  --reuse-job "<PREVIOUS_PROBE_OUTPUT>" \
  --checkpoint160 "<CHECKPOINT_160>" \
  --output "<EXTENDED_PROBE_OUTPUT>" \
  --gpus 0,1,2,3,4,5,6,7 --batch-size 128
```

输出目录必须全新，GPU布局须与原job一致。仅新增160轮特征与线性头，20／100轮读出和DINO PCA不重新拟合；
原产物只读保留，并核对新旧逐卡窗口、噪声、历史图像摘要。报告增加160−20、160−100的分来源配对组区间。
此项是train／val冻结先验验证；完整test动作指标另按原test协议评估，二者的预测目标与样本不能混同。

## 完整token等参数读出对照

`probe_tokens` 提取第100轮的完整 `one_step_hidden [B,11,768]`，复用 `probe_prior` 输出的
样本选择、标签、DINO和逐窗噪声，不重新扫描归档或拟合原来的ridge。
同一次专家前向的hidden分别取历史／当前6个、未来5个和全部11个，另设历史6帧的DINO 30-token基线。
未来hidden仍经过历史图像条件和全窗口attention；此对照只检验token读取价值，不能证明历史重建监督的因果收益。
四组都预测未来5帧的双腕位移、相机地面参考系XY位移与转向、双脚接触和相对当前帧的接触状态变化，
共70维编码目标。位移统一在当前帧固定的地面参考系中计算；接触变化指端点状态不同，
不表示两个时刻之间曾发生过任意切换。本实验不测量完整245维动作的重建误差。

```bash
python -u \
  -m MotionExpert.probe_tokens \
  --reuse-job "<PREVIOUS_PROBE_OUTPUT>" \
  --job-dir "<TOKEN_PROBE_OUTPUT>" \
  --gpus 0,1,2,3,4,5,6,7 --batch-size 128 --sleep-seconds 12 --memory-fraction .06

python -u \
  -m MotionExpert.token_probe_fit \
  --job "<TOKEN_PROBE_OUTPUT>" \
  --device cuda:0 --batch-size 256 --max-epochs 40 --patience 6 \
  --seeds 17 29 43 --sleep-seconds .02
```

提取必须保持基线的batch大小与逻辑分组；当前为B128。硬top-k MoE在不同batch的浮点舍入下可能改变路由，
因此通过增加休眠限速，不缩小batch或放宽旧特征配对容差。物理GPU子集可逐波执行原8个逻辑分片。
只在提取验收完成后运行读出。四组均使用4个可学习query的attention汇聚和70维线性输出，
每组严格为290,886个可训练参数，不在读出前mean pooling。
运动768维按固定半正交矩阵等距升为1024维；DINO保留原生1024维，不做PCA或降维。
三个运动分支共享同一变换和统计；时间编码保留原索引，DINO保留CLS/register身份并屏蔽无效图像token。
等参数量不代表特征内在秩、编码器或输入token计算量完全相同。

每个seed的四组使用相同初始化和批次顺序；只在原train内部人物／录制连通组holdout选择轮数，
再从相同初始化用全train拟合，val只评分。特征及目标统计分别仅由当前拟合分区估计。
报告三个独立读出seed的指标均值、标准差、逐seed配对连通组区间，以及RMSE、接触切换和有效覆盖。
三个seed不是三次MotionExpert训练，也不将预测集成为一个结果。
三个seed复用同一逐窗噪声，不估计更换噪声或重新训练专家带来的不确定性。
attention 读出与 mean＋ridge、DINO PCA＋ridge 使用不同的特征处理和读出方式。

产物保存在独立job：`tokens.npy`、`image-valid.npy`、`extraction-complete.json`、
`token-*-head.pt`、`token-metrics.json`、`token-report.md`及各阶段GPU检查。
优先使用空闲GPU；共享训练GPU时会争用算力，应明确记录并限速，不能保证零吞吐影响。
`control.json` 和 `fit-control.json` 的 `paused`／`sleep_seconds` 仅控制诊断，不操作训练。
