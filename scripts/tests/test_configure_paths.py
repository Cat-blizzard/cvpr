"""Portable configuration regression tests; no models, datasets or GPUs required."""

from copy import deepcopy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "configure_paths.py"
SPEC = importlib.util.spec_from_file_location("configure_paths", SCRIPT)
config = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(config)


class ConfigurePathsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="cvpr portable ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.machine = self.root / "settings/machine.json"
        self.machine.parent.mkdir()
        self.settings = {
            "data_root": "../data with spaces",
            "model_root": "../models",
            "run_root": "../runs",
        }
        self.save_machine()

    def save_machine(self):
        self.machine.write_text(json.dumps(self.settings), encoding="utf-8")

    def test_preserves_every_nonpath_motion_setting_and_default_dino(self):
        files, manifest = config.build_files(self.machine)
        actual = json.loads(files["motion.local.json"])
        original = deepcopy(config.load_motion_recipe())
        for key in ("ARCHIVE_ROOT", "SPLIT_MANIFEST", "STATS_PATH", "VISION_PROFILE_ROOT", "WINDOW_CACHE_ROOT"):
            self.assertNotEqual(actual["DATA"][key], original["DATA"][key])
            actual["DATA"].pop(key)
            original["DATA"].pop(key)
        actual["TRAIN"].pop("EXP_PATH")
        original["TRAIN"].pop("EXP_PATH")
        self.assertEqual(actual, original)
        self.assertEqual(json.loads(files["dino.local.json"]), json.loads(config.DINO_RECIPE.read_text(encoding="utf-8")))
        self.assertEqual(manifest["paths"]["data_root"], str((self.root / "data with spaces").resolve()))
        self.assertEqual(set(files), {"motion.local.json", "dino.local.json", "psi.local.env", "paths.resolved.json"})

    def test_overrides_each_path_and_requires_existing_local_dino(self):
        model = self.root / "pinned dino"
        model.mkdir()
        for key in config.OPTIONAL_KEYS:
            self.settings[key] = str(model if key == "dino_checkpoint" else self.root / key)
        self.save_machine()
        files, manifest = config.build_files(self.machine)
        motion = json.loads(files["motion.local.json"])
        self.assertEqual(motion["DATA"]["ARCHIVE_ROOT"], str(self.root / "archive_root"))
        self.assertEqual(motion["DATA"]["SPLIT_MANIFEST"], str(self.root / "archive_root/meta/splits.json"))
        self.assertEqual(motion["DATA"]["STATS_PATH"], str(self.root / "stats_path"))
        self.assertEqual(motion["DATA"]["VISION_PROFILE_ROOT"], str(self.root / "vision_profile_root"))
        self.assertEqual(motion["DATA"]["WINDOW_CACHE_ROOT"], str(self.root / "window_cache_root"))
        self.assertEqual(motion["TRAIN"]["EXP_PATH"], str(self.root / "motion_output_dir"))
        dino = json.loads(files["dino.local.json"])
        self.assertEqual(dino["checkpoint"], str(model))
        self.assertEqual(dino["revision"], "local")
        self.assertEqual(manifest["paths"]["dino_checkpoint"], str(model))
        self.settings["dino_checkpoint"] = str(self.root / "missing model")
        self.save_machine()
        with self.assertRaisesRegex(ValueError, "existing local model directory"):
            config.build_files(self.machine)

    def test_generated_json_loads_through_existing_motion_loader(self):
        files, manifest = config.build_files(self.machine)
        output = self.root / "motion.local.json"
        output.write_text(files["motion.local.json"], encoding="utf-8")
        spec = importlib.util.spec_from_file_location("motion_config_for_portability_test", config.REPO / "MotionExpert/config.py")
        motion_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(motion_config)
        with patch.dict(os.environ):
            os.environ.pop("MOTIONEXPERT_DATA_DIR", None)
            loaded = motion_config.load_config(output)
        self.assertEqual(loaded.DATA.ARCHIVE_ROOT, manifest["paths"]["archive_root"])
        self.assertEqual(loaded.DATA.DATA_DIR, manifest["paths"]["archive_root"])
        self.assertEqual(loaded.DATA.STATS_PATH, manifest["paths"]["stats_path"])
        self.assertEqual(loaded.DATA.WINDOW_CACHE_ROOT, manifest["paths"]["window_cache_root"])
        self.assertEqual(loaded.TRAIN.EXP_PATH, manifest["paths"]["motion_output_dir"])
        self.assertEqual(loaded.TRAIN.WARMUP_EPOCHS, 10)
        motion_config.validate_architecture(loaded)

    def test_environment_and_home_expansion_with_relative_machine_paths(self):
        with patch.dict(os.environ, {"CVPR_PORTABLE_TEST_ROOT": str(self.root)}):
            self.settings.update({
                "data_root": "${CVPR_PORTABLE_TEST_ROOT}/data with spaces",
                "model_root": "$CVPR_PORTABLE_TEST_ROOT/models",
                "run_root": "%CVPR_PORTABLE_TEST_ROOT%/runs",
            })
            self.save_machine()
            local = config.read_machine(self.machine)
        self.assertEqual(local["data_root"], self.root / "data with spaces")
        self.assertEqual(local["model_root"], self.root / "models")
        self.assertEqual(local["run_root"], self.root / "runs")
        self.assertEqual(config.resolve_path("~/cvpr-data", base=self.root, label="test"), Path.home() / "cvpr-data")

    def test_accepts_utf8_bom_machine_file_from_windows_editors(self):
        self.machine.write_text(json.dumps(self.settings), encoding="utf-8-sig")
        self.assertTrue(self.machine.read_bytes().startswith(b"\xef\xbb\xbf"))
        local = config.read_machine(self.machine)
        self.assertEqual(local["data_root"], (self.root / "data with spaces").resolve())
        files, _ = config.build_files(self.machine)
        self.assertIn("motion.local.json", files)

    def test_rejects_unknown_missing_invalid_or_unresolved_paths(self):
        bad_values = [
            ({**self.settings, "data_rooot": "typo"}, "Unknown"),
            ({"data_root": "../data"}, "Missing"),
            ({**self.settings, "data_root": "${CVPR_PORTABLE_UNSET}"}, "unset environment"),
            ({**self.settings, "data_root": "${broken"}, "unresolved"),
            ({**self.settings, "data_root": "~cvpr_nonexistent_user_28732/data"}, "home directory"),
            ({**self.settings, "run_root": str(config.REPO / "runs")}, "outside"),
            ({**self.settings, "model_root": 2}, "path string"),
            ({**self.settings, "data_root": "x\ny"}, "newline"),
        ]
        with patch.dict(os.environ, {}, clear=True):
            for values, message in bad_values:
                with self.subTest(values=values):
                    self.machine.write_text(json.dumps(values), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        config.read_machine(self.machine)

    def test_dry_run_is_independent_of_cwd_and_creates_nothing(self):
        other_cwd = self.root / "different cwd"
        other_cwd.mkdir()
        output = self.root / "not created/configs"
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--machine", str(self.machine), "--output-dir", str(output), "--dry-run"],
            cwd=other_cwd, text=True, encoding="utf-8", capture_output=True, check=True,
        )
        plan = json.loads(result.stdout)
        self.assertTrue(plan["dry_run"])
        self.assertEqual(plan["paths"]["data_root"], str((self.root / "data with spaces").resolve()))
        self.assertFalse(output.parent.exists())
        self.assertFalse((self.root / "runs").exists())
        self.assertFalse((self.root / "data with spaces").exists())

    def test_no_clobber_preflights_all_targets_and_force_is_explicit(self):
        files, _ = config.build_files(self.machine)
        output = self.root / "generated"
        output.mkdir()
        protected = output / "psi.local.env"
        protected.write_text("personal config\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
            config.write_files(output, files)
        self.assertEqual(sorted(p.name for p in output.iterdir()), ["psi.local.env"])
        self.assertEqual(protected.read_text(encoding="utf-8"), "personal config\n")
        unrelated = output / "unrelated.txt"
        unrelated.write_text("keep", encoding="utf-8")
        config.write_files(output, files, force=True)
        self.assertEqual(protected.read_text(encoding="utf-8"), files["psi.local.env"])
        self.assertEqual(unrelated.read_text(encoding="utf-8"), "keep")
        for name in files:
            self.assertEqual((output / name).read_text(encoding="utf-8"), files[name])

    def test_missing_model_cli_fails_without_partial_output(self):
        self.settings["dino_checkpoint"] = str(self.root / "missing")
        self.save_machine()
        output = self.root / "output"
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--machine", str(self.machine), "--output-dir", str(output)],
            cwd=self.root, text=True, encoding="utf-8", capture_output=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("existing local model directory", result.stderr)
        self.assertFalse(output.exists())

    def test_env_values_roundtrip_spaces_quotes_and_windows_separators(self):
        try:
            from dotenv import dotenv_values
        except ImportError:
            self.skipTest("python-dotenv is only required for VLM environments")
        text = "C:\\external data\\a'b#c"
        self.assertEqual(dotenv_values(stream=io.StringIO("TEST=" + config.dotenv_value(text)))["TEST"], text)
        files, _ = config.build_files(self.machine)
        env = dotenv_values(stream=io.StringIO(files["psi.local.env"]))
        self.assertEqual(env["PSI_HOME"], str(self.root / "runs/psi"))
        self.assertEqual(env["DATA_HOME"], str(self.root / "data with spaces"))
        self.assertEqual(env["HF_LEROBOT_HOME"], str(self.root / "data with spaces/lerobot"))
        self.assertNotIn("HF_TOKEN", env)
        self.assertNotIn("WANDB_API_KEY", env)


if __name__ == "__main__":
    unittest.main()
