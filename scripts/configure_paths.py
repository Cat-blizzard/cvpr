"""Generate machine-local configs without changing accepted training sources."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


REPO = Path(__file__).resolve().parents[1]
DEFAULT_MACHINE = REPO / "configs/machines/local.example.json"
MOTION_RECIPE = REPO / "MotionExpert/configs/smplh_k12_psi0_pretrain.yaml"
DINO_RECIPE = REPO / "pipeline/configs/dino.example.json"
ROOT_KEYS = {"data_root", "model_root", "run_root"}
OPTIONAL_KEYS = {
    "archive_root", "stats_path", "vision_profile_root", "window_cache_root",
    "motion_output_dir", "dino_checkpoint",
}
VARIABLE = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))|%([A-Za-z_][A-Za-z0-9_]*)%")


def resolve_path(value, *, base, label):
    """Resolve local paths consistently, independent of the caller's cwd."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty path string")
    if any(char in value for char in ("\n", "\r", "\0")):
        raise ValueError(f"{label} must not contain a newline or NUL")

    def substitute(match):
        name = next(group for group in match.groups() if group is not None)
        if name not in os.environ or not os.environ[name]:
            raise ValueError(f"{label} references unset environment variable {name}")
        return os.environ[name]

    expanded = VARIABLE.sub(substitute, value)
    if "${" in expanded or VARIABLE.search(expanded):
        raise ValueError(f"{label} contains an unresolved environment placeholder")
    if any(char in expanded for char in ("\n", "\r", "\0")):
        raise ValueError(f"{label} expands to a newline or NUL")
    try:
        path = Path(expanded).expanduser()
    except RuntimeError as error:
        raise ValueError(f"{label} contains an unresolved home directory") from error
    if str(path).startswith("~"):
        raise ValueError(f"{label} contains an unresolved home directory")
    return (path if path.is_absolute() else base / path).resolve()


def outside_checkout(path, label):
    if path == REPO or path.is_relative_to(REPO):
        raise ValueError(f"{label} must be outside the repository checkout: {path}")
    return path


def read_machine(machine_path):
    values = json.loads(machine_path.read_text(encoding="utf-8-sig"))
    if not isinstance(values, dict):
        raise ValueError("Machine config must be a JSON object")
    unknown = set(values) - ROOT_KEYS - OPTIONAL_KEYS
    if unknown:
        raise ValueError("Unknown machine config keys: " + ", ".join(sorted(unknown)))
    missing = ROOT_KEYS - set(values)
    if missing:
        raise ValueError("Missing machine config keys: " + ", ".join(sorted(missing)))
    return {
        key: outside_checkout(resolve_path(value, base=machine_path.parent, label=key), key)
        for key, value in values.items()
    }


def load_motion_recipe():
    try:
        import yaml
    except ImportError as error:
        raise ValueError("PyYAML is required; install the MotionExpert dependencies or run python -m pip install PyYAML") from error
    try:
        recipe = yaml.safe_load(MOTION_RECIPE.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid Motion recipe: {error}") from error
    if not isinstance(recipe, dict):
        raise ValueError("Motion recipe must be a YAML mapping")
    return recipe


def dotenv_value(value):
    # Preserve spaces, #, quotes and Windows separators in python-dotenv values.
    # Path placeholders have already been resolved before reaching this function.
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def build_files(machine_path):
    local = read_machine(machine_path)
    data = local["data_root"]
    model = local["model_root"]
    runs = local["run_root"]
    mixed = data / "MixEgoMotion"
    archive = local.get("archive_root", mixed / "smplh-parameters-v4-camera-quality")
    paths = {
        "data_root": data,
        "model_root": model,
        "run_root": runs,
        "archive_root": archive,
        "split_manifest": archive / "meta/splits.json",
        "stats_path": local.get("stats_path", mixed / "statistics/smplh_k12_5hz_joint_camera-quality-v4.pt"),
        "vision_profile_root": local.get("vision_profile_root", archive / "vision_profiles/psi0_256x480_v1_30hz"),
        "window_cache_root": local.get("window_cache_root", mixed / "training_cache/smplh245_5hz_w11_camera-quality-v4"),
        "motion_output_dir": local.get("motion_output_dir", runs / "motion/smplh_k12_psi0_256x480_5hz_camera_quality_v4_meanpool_from_scratch"),
    }
    paths = {key: str(outside_checkout(path.resolve(), key)) for key, path in paths.items()}
    motion = deepcopy(load_motion_recipe())
    motion["DATA"].update({
        "ARCHIVE_ROOT": paths["archive_root"],
        "SPLIT_MANIFEST": paths["split_manifest"],
        "STATS_PATH": paths["stats_path"],
        "VISION_PROFILE_ROOT": paths["vision_profile_root"],
        "WINDOW_CACHE_ROOT": paths["window_cache_root"],
    })
    motion["TRAIN"]["EXP_PATH"] = paths["motion_output_dir"]
    dino = json.loads(DINO_RECIPE.read_text(encoding="utf-8"))
    if "dino_checkpoint" in local:
        checkpoint = local["dino_checkpoint"]
        if not checkpoint.is_dir():
            raise ValueError(f"dino_checkpoint must be an existing local model directory: {checkpoint}")
        dino.update(checkpoint=str(checkpoint), revision="local")
        paths["dino_checkpoint"] = str(checkpoint)
    env = {
        "CVPR_DATA_ROOT": data,
        "CVPR_MODEL_ROOT": model,
        "CVPR_RUN_ROOT": runs,
        "PSI_HOME": runs / "psi",
        "DATA_HOME": data,
        "HF_HOME": runs / "cache/huggingface",
        "TORCH_HOME": runs / "cache/torch",
        "UV_CACHE_DIR": runs / "cache/uv",
        "HF_LEROBOT_HOME": data / "lerobot",
    }
    for key, path in env.items():
        outside_checkout(path.resolve(), key)
    manifest = {
        "machine_config": str(machine_path),
        "paths": paths,
        "sources": {
            recipe.relative_to(REPO).as_posix(): hashlib.sha256(recipe.read_bytes()).hexdigest()
            for recipe in (MOTION_RECIPE, DINO_RECIPE)
        },
        "boundary": "Path configuration only; data, weight identity, cache and GPU acceptance are not verified or rewritten.",
    }
    def dump(value):
        return json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    files = {
        "motion.local.json": dump(motion),
        "dino.local.json": dump(dino),
        "psi.local.env": "# Generated dotenv file; load with python-dotenv, not shell source.\n"
        + "\n".join(f"{key}={dotenv_value(value)}" for key, value in env.items()) + "\n",
        "paths.resolved.json": dump(manifest),
    }
    return files, manifest


def write_files(output_dir, files, *, force=False):
    targets = {name: output_dir / name for name in files}
    existing = [str(path) for path in targets.values() if path.exists() or path.is_symlink()]
    if existing and not force:
        raise ValueError("Refusing to overwrite local config files; use --force explicitly: " + ", ".join(existing))
    if any(path.is_dir() for path in targets.values()):
        raise ValueError("A config output path is a directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    # Validate everything before writing; stage complete files on the same filesystem.
    # Each replacement is atomic. Existing local configs require explicit --force.
    with tempfile.TemporaryDirectory(prefix=".configure-paths-", dir=output_dir) as temporary:
        staged = Path(temporary)
        for name, content in files.items():
            (staged / name).write_text(content, encoding="utf-8", newline="\n")
        if force:
            for name, target in targets.items():
                os.replace(staged / name, target)
        else:
            created = []
            try:
                # Exclusive creation prevents a late-arriving file from being overwritten.
                for name, target in targets.items():
                    with target.open("xb") as handle:
                        created.append(target)
                        handle.write((staged / name).read_bytes())
            except OSError:
                for target in created:
                    target.unlink(missing_ok=True)
                raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--machine", type=Path, default=DEFAULT_MACHINE,
                        help="Optional machine JSON; defaults to the bundled directory layout (relative paths resolve against this file)")
    parser.add_argument("--output-dir", type=Path, default=REPO / ".local/configs", help="Generated configs; relative paths resolve against the current directory")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved paths without creating files or running any workload")
    parser.add_argument("--force", action="store_true", help="Explicitly replace previously generated config files")
    args = parser.parse_args(argv)
    try:
        machine = args.machine.expanduser().resolve(strict=True)
        output = args.output_dir.expanduser().resolve()
        files, manifest = build_files(machine)
        if not args.dry_run:
            write_files(output, files, force=args.force)
        print(json.dumps({
            "dry_run": args.dry_run,
            "output_dir": str(output),
            "files": [str(output / name) for name in files],
            **manifest,
        }, indent=2, ensure_ascii=True))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
