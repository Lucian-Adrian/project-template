import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "config" / "deploy.sh"
DIRECTORIES = (
    ".github", "config", "docs", "docs/backend", "docs/db",
    "docs/frontend", "docs/info", "docs/tests",
)
FILES = (
    ".github/copilot-instructions.md", "docs/file-structure.md", "changelog.md",
    "contributing.md", "readme.md", "config/.editorconfig", "config/Dockerfile",
    "config/docker-compose.yml", ".gitignore",
)


class DeployTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name) / "project with spaces"
        self.project.mkdir()

    def run_deploy(self, answers=""):
        # The script deletes itself, so always execute a disposable copy.
        script = self.project / "deploy copy.sh"
        shutil.copyfile(SCRIPT, script)
        result = subprocess.run(
            ["bash", script.name], cwd=self.project, input=answers,
            text=True, capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, "Scaffolder failed")
        self.assertFalse(script.exists())
        return result

    def write_existing(self, name, content):
        target = self.project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def test_fresh_scaffolding_in_directory_with_spaces(self):
        self.run_deploy()
        for directory in DIRECTORIES:
            self.assertTrue((self.project / directory).is_dir(), directory)
        for name in FILES:
            self.assertTrue((self.project / name).is_file(), name)
            self.assertGreater((self.project / name).stat().st_size, 0, name)

    def test_rerun_preserves_nested_sentinels_when_accepting_overwrites(self):
        self.run_deploy()
        sentinels = [
            self.write_existing(f"{directory}/nested/keep.txt", "keep\n")
            for directory in DIRECTORIES
        ]
        self.run_deploy("y\n" * len(FILES))
        for sentinel in sentinels:
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep\n")

    def test_file_overwrite_choices_are_independent(self):
        skipped = self.write_existing(FILES[0], "keep instructions\n")
        replaced = self.write_existing(FILES[1], "old structure\n")
        self.run_deploy("n\nY\n")
        self.assertEqual(skipped.read_text(encoding="utf-8"), "keep instructions\n")
        self.assertTrue(replaced.read_text(encoding="utf-8").startswith(
            "# Project File Structure\n"))
        self.assertTrue((self.project / FILES[-1]).is_file())

    def test_empty_answer_skips_file(self):
        target = self.write_existing(FILES[0], "keep\n")
        self.run_deploy("\n")
        self.assertEqual(target.read_text(encoding="utf-8"), "keep\n")

    def test_eof_preserves_all_existing_files_and_creates_missing_files(self):
        targets = [self.write_existing(name, "keep\n") for name in FILES[:-1]]
        self.run_deploy()
        for target in targets:
            self.assertEqual(target.read_text(encoding="utf-8"), "keep\n")
        self.assertTrue((self.project / FILES[-1]).is_file())

    def test_eof_after_unterminated_yes_skips_file(self):
        target = self.write_existing(FILES[0], "keep\n")
        self.run_deploy("y")
        self.assertEqual(target.read_text(encoding="utf-8"), "keep\n")
