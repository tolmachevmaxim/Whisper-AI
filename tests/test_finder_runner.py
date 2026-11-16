"""Check Finder interpreter selection without loading transcription models."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which("zsh"), "Finder runner requires zsh")
class FinderRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "Whisper checkout"
        self.runner = self.root / "tools/macos/transcribe_from_finder.zsh"
        self.runner.parent.mkdir(parents=True)
        source = Path(__file__).resolve().parents[1] / "tools/macos/transcribe_from_finder.zsh"
        shutil.copy2(source, self.runner)
        self.script = self.root / "skill/scripts/transcribe.py"
        self.script.parent.mkdir(parents=True)
        self.script.write_text("# Stub: never executed by these tests.\n")

    def interpreter(self, relative):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('#!/bin/zsh\nprintf "%s\\n" "$0" "$PWD" "$WHISPER_PROJECT_DIR" "$@"\n')
        path.chmod(0o755)
        return path

    def run_runner(self, *args, override=None):
        # Keep the test independent of the user's Python override.
        import os
        env = dict(os.environ)
        env.pop("WHISPER_PYTHON_BIN", None)
        if override is not None:
            env["WHISPER_PYTHON_BIN"] = str(override)
        return subprocess.run(["zsh", str(self.runner), *args], env=env,
                              capture_output=True, text=True)

    def assert_launch(self, result, python, args):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(),
                         [str(python), str(self.root), str(self.root), str(self.script), *args])

    def test_prefers_dotvenv_and_preserves_arguments(self):
        python = self.interpreter(".venv/bin/python3")
        self.interpreter("venv/bin/python3")
        args = ["--persons", "a recording's name.wav", "--all-outputs"]
        self.assert_launch(self.run_runner(*args), python, args)

    def test_falls_back_to_legacy_venv(self):
        python = self.interpreter("venv/bin/python3")
        self.assert_launch(self.run_runner("audio.wav"), python, ["audio.wav"])

    def test_explicit_override_wins(self):
        self.interpreter(".venv/bin/python3")
        python = self.interpreter("custom python")
        self.assert_launch(self.run_runner("audio.wav", override=python), python, ["audio.wav"])

    def test_missing_environment_reports_supported_setup(self):
        result = self.run_runner("audio.wav")
        self.assertEqual(result.returncode, 127)
        self.assertIn("python3 -m venv venv", result.stderr)
        self.assertNotIn("uv sync", result.stderr)

    def test_invalid_override_does_not_silently_fall_back(self):
        self.interpreter(".venv/bin/python3")
        result = self.run_runner(override=self.root / "missing-python")
        self.assertEqual(result.returncode, 126)
        self.assertIn("not executable", result.stderr)

    def test_missing_transcriber_fails_before_execution(self):
        self.interpreter(".venv/bin/python3")
        self.script.unlink()
        result = self.run_runner()
        self.assertEqual(result.returncode, 127)
        self.assertIn("Transcribe script not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
