# Σ₀: From Human Interaction and Motion to Humanoid Loco-Manipulation

**English** | [简体中文](README.zh-CN.md)

## Abstract

Humanoid loco-manipulation requires a robot to preserve a hand-object interaction while adapting its whole-body motion across varying initial states. Collecting synchronized whole-body teleoperation demonstrations is costly, yet egocentric videos offer scalable supervision at different action granularities: fine-grained wrist and fingertip trajectories capture object interaction, whereas sparse skeletal motion describes whole-body coordination. This supervision--execution asymmetry motivates learning the two priors separately and coupling them during robot control. We present Σ₀, a vision-language-action framework that learns an interaction prior through hand-action prediction and a coordination prior by jointly reconstructing observed skeletal motion and forecasting its future evolution. During robot-supervised post-training, the policy integrates both priors through proprioception-conditioned serial cross-attention, directly predicting robot-native body and hand actions without retargeting human motion. Across six SIMPLE tasks, Σ₀ achieves 92.8% success, surpassing the strongest baseline by 8.1 percentage points. With 10 demonstrations per task, Σ₀ achieves 83.3% success, whereas the variant without human-prior pretraining achieves 75.0% with 100 demonstrations per task. These results support data-efficient humanoid control from complementary human priors.

## Installation

## Configuration

Run the commands below from the repository root and replace `<...>` placeholders with your paths and values. The configuration tool requires PyYAML.

```bash
mkdir -p .local
cp configs/machines/local.example.json .local/machine.json
# Edit data_root, model_root and run_root in .local/machine.json.
python scripts/configure_paths.py --machine .local/machine.json
```

Store datasets, model weights and outputs outside the checkout. The default roots are `~/cvpr-data`, `~/cvpr-models` and `~/cvpr-runs`.

The tool writes the following files to `.local/configs/`:

| File | Use |
| --- | --- |
| `motion.local.json` | MotionExpert training and evaluation configuration. |
| `dino.local.json` | DINO feature extraction configuration. |
| `psi.local.env` | Path variables to merge into `VLMExpert/.env`. |
| `paths.resolved.json` | Resolved data, model and output paths. |

Use `--dry-run` to preview paths, `--output-dir` to choose another configuration directory, and `--force` to replace existing configuration files.

<details>
<summary>Optional path overrides</summary>

Add these fields to `.local/machine.json` when resources are stored separately:

| Field | Resource |
| --- | --- |
| `archive_root` | SMPL-H motion archive. |
| `stats_path` | Motion normalization statistics. |
| `vision_profile_root` | DINO feature directory. |
| `window_cache_root` | Motion training window cache. |
| `motion_output_dir` | Motion training output directory. |
| `dino_checkpoint` | Existing local DINO model directory; otherwise the pinned official model is used. |

Relative paths resolve against the machine JSON file. Paths support `~`, `$NAME` and `${NAME}`. Motion archive selection follows `--data-dir`, then `MOTIONEXPERT_DATA_DIR`, then the configuration file.

</details>

## Data Preparation

Raw data downloaders:

```bash
python datasets/download_egosuite.py run \
  --output-dir "<DATA_ROOT>/EgoSuite" --hours "<HOURS>"

python datasets/download_egoexo4d_hm.py \
  --output-dir "<DATA_ROOT>/EgoExo-4D-HM" \
  --aws-profile "<AWS_PROFILE>" --take "<TAKE_NAME>"
```

Motion training uses an SMPL-H archive, split manifest, normalization statistics, DINO features and a window cache. See [MotionExpert](MotionExpert/README.md) for archive and cache preparation, and [data formats](docs/protocols/README.md) for model inputs.

Extract DINO features from the archive and its original camera videos:

```bash
python -m egomotion_pipeline.cli extract-smplh-features \
  --dataset "<ARCHIVE_ROOT>" \
  --output "<VISION_ROOT>" \
  --config .local/configs/dino.local.json
```

Set `vision_profile_root` in `.local/machine.json` to the resulting feature directory and regenerate the configuration. Feature extraction options are described in [pipeline](pipeline/README.md).

```bash
python scripts/configure_paths.py --machine .local/machine.json --force
```

## Training

### MotionExpert

```bash
python -m MotionExpert.train --config .local/configs/motion.local.json --from-scratch
```

The recipe defaults to 8 GPUs and batch256 per GPU. Adjust `--devices`, `--batch-size` and `--num-workers` for your run.

To resume, replace `--from-scratch` with `--resume`:

```bash
python -m MotionExpert.train --config .local/configs/motion.local.json \
  --resume "<CHECKPOINT>"
```

### Dual-source action expert

Copy the [UnifoLM environment example](configs/machines/unifolm.env.example.sh) and set the dataset paths, VLM weights, Motion checkpoint and DINO cache:

```bash
cp configs/machines/unifolm.env.example.sh .local/unifolm.env.sh
# Edit .local/unifolm.env.sh.
source .local/unifolm.env.sh
bash VLMExpert/scripts/train/psi0/posttrain-dual-source-unifolm.sh
```

The dual-source policy uses six real DINO observations at 5Hz, with the final observation aligned to the VLM image. Model and training options are described in [VLMExpert](VLMExpert/README.md).

## Evaluation

```bash
python -m MotionExpert.evaluate \
  --checkpoint "<CHECKPOINT>" \
  --config .local/configs/motion.local.json \
  --split val --max-samples "<NUM_SAMPLES>" \
  --output "<OUTPUT_PATH>"
```

Choose `val` or `test` with `--split` and set the number of samples with `--max-samples`. Motion inference and hidden-feature extraction are described in [MotionExpert](MotionExpert/README.md).

For policy serving and simulation, see [SIMPLE tools](scripts/4090_simple/README.md). PICO recording instructions are in [teleoperation](docs/teleoperation.md).

## Code Structure

| Component | Description |
| --- | --- |
| [MotionExpert](MotionExpert/README.md) | Human motion prior and motion forecasting. |
| [ImageProcess](ImageProcess/README.md) | Shared image preprocessing and augmentation. |
| [pipeline](pipeline/README.md) | DINO feature extraction. |
| [VLMExpert](VLMExpert/README.md) | Vision-language backbone and dual-source action expert. |

## Acknowledgements

This project builds on [Ψ₀](https://github.com/physical-superintelligence-lab/Psi0). See [third-party code](docs/dependencies/README.md) for sources and licenses.
