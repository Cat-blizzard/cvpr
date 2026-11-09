# 数据与模型协议历史快照

保存自整理前的 `AGENTS.md`（提交 `70d62a4`），日期为 2026-11-09。
本页保留当时的任务状态、原始路径和既有授权描述用于追溯；这些描述不构成新机器启动训练的授权或当前验收证明。
当前协议入口见[协议说明](../protocols/README.md)。

## 4. 当前数据与模型协议

### 运动协议

- 训练目标为继承双来源最终FK验收并完成相机原生质量修订的SMPL-H参数归档：
  `/gaozt-test1/datasets/MixEgoMotion/smplh-parameters-v4-camera-quality`
- 新归档、窗口缓存及全量train统计验收完成后才能启动训练；原v1/v2/v3与现有checkpoint保留追溯。
- 当前架构为e7_smplh12_hands21_meanpool_qkvnorm_v2；删除可学习GLOBAL，11个motion hidden直接mean pooling。self-attention Q/K/V全归一化，cross context独立归一化。旧GLOBAL/旧注意力checkpoint不兼容，旧第60轮专用配置已移除；正式配置显式设置从头新任务200轮、10轮warmup、峰值LR1e-4。归档、缓存、统计及GPU验收已完成，用户已授权八卡、每卡256、24worker正式训练。
- HM检查原始MPS质量及closed/open-loop连续性；EgoSuite没有源confidence，不伪造。5Hz参考增量必须检查中间所有30Hz点及边。相机质量失败不删除独立world观测或DINO。
- 训练更新前检查全卡loss/activation、unscale后clip前梯度，异常一致停止并保存batch/RNG诊断；正式就绪绑定新缓存、全train统计和当前架构GPU验收。
- 当前单机八卡启用NCCL P2P／共享内存（IB关闭），正式启动不用 `--ddp-socket`；批量指标同步开启，普通AdamW与逐步异常保护保留。通信改动须验证实际P2P/IPC路径及连续多步跨卡参数一致性。
- 保留双手各21点、相机轨迹、地面、有效 mask 和原始分割。
- MotionExpert 使用5Hz、11帧：
  历史5帧＋当前帧，预测未来5帧。
- Ψ₀ 当前图像对应 MotionExpert 历史6帧中的最后一帧。
- 运动表示为245维，相机轨迹为18维。
- 身体使用既定K12，保留6D旋转、XYZ、双手显式监督、参考运动与脚接触。
- 最终FK头部必须通过相机及有效源头部观测的物理一致性筛选。EgoSuite失败时屏蔽拟合身体，保留独立源手/脚/相机；HM拟合关联手脚随身体失效。
- 坐标采用相机地面投影参考系，单位为米，世界坐标Z-up。
- 6D旋转编码取旋转矩阵前两行。
- 标签 mask 用于监督；未来标签可用性不得影响部署输入。
- t=1 使用完整高斯噪声，缺失标签通道不能被清零。
- 一步 hidden 接口保留反传能力，DINO编码器保持冻结。

### 视觉协议

- 使用 dinov2-with-registers-large，输出CLS＋4个register，即5×1024。
- 离线特征保存原生30Hz；训练读取历史6个5Hz时刻。
- DINO按episode保存 features.npy，使用mmap按需读取。
- 预训练：H256×W480。
- 后训练：H256×W320。
- Robust：H256×W480。
- 通用 `shared_rgb` 模式：两路复用同一份处理后的当前RGB，各自进行编码器归一化；在线增强每窗口采样一次，颜色和随机裁切参数在整个历史窗口内共享。
- 当前 UnifoLM 后训练显式使用 `motion_image_policy="vlm_color_clean_motion"`：两路当前帧保持同源、同时间、同 `256x320` 几何 profile；仅 VLM 当前帧在训练时做 ImageProcess 的 Ψ₀ 颜色增强，Motion 历史6帧全部使用现有 clean DINO 缓存。本策略不启用随机裁切，验证／`no_aug`／推理保持 clean；不因该颜色策略重做缓存或改写缓存 metadata。
- `shared_rgb` 仍为兼容默认值；若增强 Motion 输入，仍须在线编码同步增强后的完整历史窗口，不能用 clean DINO 特征替代。DINO 始终冻结，MotionExpert 可按训练配置参与反传。
- 跨视觉尺寸适配须明确声明，DINO权重身份和归一化仍须匹配。

协议变更时，同步更新实现、配置、接口说明和相关验证。
