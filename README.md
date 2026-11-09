# Σ₀: From Human Interaction and Motion to Humanoid Loco-Manipulation

**English** | [简体中文](README.zh-CN.md)

## Abstract

Humanoid loco-manipulation requires a robot to preserve a hand-object interaction while adapting its whole-body motion across varying initial states. Collecting synchronized whole-body teleoperation demonstrations is costly, yet egocentric videos offer scalable supervision at different action granularities: fine-grained wrist and fingertip trajectories capture object interaction, whereas sparse skeletal motion describes whole-body coordination. This supervision--execution asymmetry motivates learning the two priors separately and coupling them during robot control. We present Σ₀, a vision-language-action framework that learns an interaction prior through hand-action prediction and a coordination prior by jointly reconstructing observed skeletal motion and forecasting its future evolution. During robot-supervised post-training, the policy integrates both priors through proprioception-conditioned serial cross-attention, directly predicting robot-native body and hand actions without retargeting human motion. Across six SIMPLE tasks, Σ₀ achieves 92.8% success, surpassing the strongest baseline by 8.1 percentage points. With 10 demonstrations per task, Σ₀ achieves 83.3% success, whereas the variant without human-prior pretraining achieves 75.0% with 100 demonstrations per task. These results support data-efficient humanoid control from complementary human priors.

## Installation

## Configuration

Generate the configuration with the default directories:

```bash
python scripts/configure_paths.py
```

The default directories are `~/sigma0/data`, `~/sigma0/models` and `~/sigma0/runs`.

The tool writes the following files to `.local/configs/`:

| File | Use |
| --- | --- |
| `motion.local.json` | MotionExpert training and evaluation configuration. |
| `dino.local.json` | DINO feature extraction configuration. |
| `psi.local.env` | Path variables to merge into `VLMExpert/.env`. |
| `paths.resolved.json` | Resolved data, model and output paths. |

Use `--dry-run` to preview paths, `--output-dir` to choose another configuration directory, and `--force` to replace existing configuration files.

<details>
<summary>Customize paths</summary>

To use different directories, copy the example, edit `data_root`, `model_root` and `run_root`, and regenerate the configuration:

```bash
mkdir -p .local
cp configs/machines/local.example.json .local/machine.json
# Edit .local/machine.json.
python scripts/configure_paths.py --machine .local/machine.json --force
```

Additional resources can be configured separately:

| Field | Resource |
| --- | --- |
| `archive_root` | SMPL-H motion archive. |
| `stats_path` | Motion normalization statistics. |
| `vision_profile_root` | DINO feature directory. |
| `window_cache_root` | Motion training window cache. |
| `motion_output_dir` | Motion training output directory. |
| `dino_checkpoint` | Existing local DINO model directory; otherwise the pinned official model is used. |

Relative paths resolve against the machine JSON file. Paths support `~`, `$NAME` and `${NAME}`. Motion archive selection follows `--data-dir`, then `MOTIONEXPERT_DATA_DIR`, then the configuration file.

Pass the same `--machine` file when regenerating a custom configuration, and use its paths in the data-preparation commands below.

</details>

## Data Preparation

Raw data downloaders:

```bash
python datasets/download_egosuite.py run \
  --output-dir "$HOME/sigma0/data/EgoSuite"

python datasets/download_egoexo4d_hm.py \
  --output-dir "$HOME/sigma0/data/EgoExo-4D-HM"
```

The HM downloader uses your configured AWS credentials. Download options, including `--hours`, `--take` and `--aws-profile`, are listed by each script's `--help`.

Motion training uses an SMPL-H archive, split manifest, normalization statistics, DINO features and a window cache. See [MotionExpert](MotionExpert/README.md) for archive and cache preparation, and [data formats](docs/protocols/README.md) for model inputs.

Extract DINO features from the archive and its original camera videos:

```bash
ARCHIVE_ROOT="$HOME/sigma0/data/MixEgoMotion/smplh-parameters-v4-camera-quality"
VISION_ROOT="$ARCHIVE_ROOT/vision_profiles/psi0_256x480_v1_30hz"

python -m egomotion_pipeline.cli extract-smplh-features \
  --dataset "$ARCHIVE_ROOT" \
  --output "$VISION_ROOT" \
  --config .local/configs/dino.local.json
```

This output directory matches the default Motion configuration. Feature extraction options are described in [pipeline](pipeline/README.md).

## Training

### MotionExpert

```bash
python -m MotionExpert.train --config .local/configs/motion.local.json --from-scratch
```

The recipe defaults to 8 GPUs and batch256 per GPU. Adjust `--devices`, `--batch-size` and `--num-workers` for your run.

Resume from the last saved checkpoint:

```bash
MOTION_RUN="$HOME/sigma0/runs/motion/smplh_k12_psi0_256x480_5hz_camera_quality_v4_meanpool_from_scratch"

python -m MotionExpert.train --config .local/configs/motion.local.json \
  --resume "$MOTION_RUN/last.ckpt"
```

### Dual-source action expert

Prepare EgoDex-pretrained VLM weights in `~/sigma0/models/egodex-vlm`. The [UnifoLM environment example](configs/machines/unifolm.env.example.sh) uses the Motion training output's `final.ckpt` and data under `~/sigma0/data/UnifoLM`:

```bash
cp configs/machines/unifolm.env.example.sh .local/unifolm.env.sh
source .local/unifolm.env.sh
bash VLMExpert/scripts/train/psi0/posttrain-dual-source-unifolm.sh
```

For other weights or datasets, adjust `.local/unifolm.env.sh`. The dual-source policy uses six real DINO observations at 5Hz, with the final observation aligned to the VLM image. Model and training options are described in [VLM Expert](VLMExpert/README.md).

## Evaluation

Evaluate the final checkpoint after Motion training:

```bash
MOTION_RUN="$HOME/sigma0/runs/motion/smplh_k12_psi0_256x480_5hz_camera_quality_v4_meanpool_from_scratch"

python -m MotionExpert.evaluate \
  --checkpoint "$MOTION_RUN/final.ckpt" \
  --config .local/configs/motion.local.json \
  --split val --max-samples 16 \
  --output "$HOME/sigma0/runs/evaluation/motion-val.json"
```

This evaluates 16 validation windows. Adjust `--checkpoint`, `--split` and `--max-samples` for other evaluations. Motion inference and hidden-feature extraction are described in [MotionExpert](MotionExpert/README.md).

For policy serving and simulation, see [SIMPLE tools](scripts/4090_simple/README.md). PICO recording instructions are in [teleoperation](docs/teleoperation.md).

## Code Structure

| Component | Description |
| --- | --- |
| [MotionExpert](MotionExpert/README.md) | Human motion prior and motion forecasting. |
| [ImageProcess](ImageProcess/README.md) | Shared image preprocessing and augmentation. |
| [pipeline](pipeline/README.md) | DINO feature extraction. |
| [VLM Expert](VLMExpert/README.md) | Vision-language backbone and dual-source action expert. |

## Acknowledgements

This project builds on [Ψ₀](https://github.com/physical-superintelligence-lab/Psi0). See [third-party code](docs/dependencies/README.md) for sources and licenses.
