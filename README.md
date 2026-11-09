# Σ₀: From Human Interaction and Motion to Humanoid Loco-Manipulation

## Abstract

Humanoid loco-manipulation requires a robot to preserve a hand-object interaction while adapting its whole-body motion across varying initial states. Collecting synchronized whole-body teleoperation demonstrations is costly, yet egocentric videos offer scalable supervision at different action granularities: fine-grained wrist and fingertip trajectories capture object interaction, whereas sparse skeletal motion describes whole-body coordination. This supervision--execution asymmetry motivates learning the two priors separately and coupling them during robot control. We present Σ₀, a vision-language-action framework that learns an interaction prior through hand-action prediction and a coordination prior by jointly reconstructing observed skeletal motion and forecasting its future evolution. During robot-supervised post-training, the policy integrates both priors through proprioception-conditioned serial cross-attention, directly predicting robot-native body and hand actions without retargeting human motion. Across six SIMPLE tasks, Σ₀ achieves 92.8% success, surpassing the strongest baseline by 8.1 percentage points. With 10 demonstrations per task, Σ₀ achieves 83.3% success, whereas the variant without human-prior pretraining achieves 75.0% with 100 demonstrations per task. These results support data-efficient humanoid control from complementary human priors.

## Installation

## Usage

- [Data preparation, training and evaluation](docs/reproduction/README.md)
- [Path configuration](configs/README.md)

## Code Structure

| Component | Description |
| --- | --- |
| [MotionExpert](MotionExpert/README.md) | Human motion prior and motion forecasting. |
| [ImageProcess](ImageProcess/README.md) | Shared image preprocessing and augmentation. |
| [pipeline](pipeline/README.md) | DINO feature extraction. |
| [VLMExpert](VLMExpert/README.md) | Vision-language backbone and dual-source action expert. |

## Acknowledgements

This project builds on [Ψ₀](https://github.com/physical-superintelligence-lab/Psi0). See [third-party code](docs/dependencies/README.md) for sources and licenses.
