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

    def run_deploy(self, answers="", expect_success=True):
        # The script deletes itself, so always execute a disposable copy.
        script = self.project / "deploy copy.sh"
        shutil.copyfile(SCRIPT, script)
        result = subprocess.run(
            ["bash", script.name], cwd=self.project, input=answers,
            text=True, capture_output=True, timeout=10,
        )
        if expect_success:
            self.assertEqual(result.returncode, 0, "Scaffolder failed")
            self.assertFalse(script.exists())
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing symlink destination:", result.stderr)
            self.assertTrue(script.exists())
        return result

    def test_symlinked_files_preserve_external_sentinels(self):
        root = self.project
        sentinel = root.parent / "external.txt"
        sentinel.write_text("keep external\n", encoding="utf-8")
        for index, name in enumerate(FILES):
            with self.subTest(path=name):
                self.project = root / str(index)
                self.project.mkdir()
                target = self.project / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(sentinel)
                self.run_deploy("y\n" * len(FILES), expect_success=False)
                self.assertTrue(target.is_symlink())
                self.assertEqual(sentinel.read_text(encoding="utf-8"),
                                 "keep external\n")

    def test_symlinked_directories_preserve_external_tree(self):
        root = self.project
        external = root.parent / "external"
        external.mkdir()
        contents = {Path(name).name: "keep external\n" for name in FILES}
        for name, content in contents.items():
            (external / name).write_text(content, encoding="utf-8")
        for index, name in enumerate(DIRECTORIES):
            with self.subTest(path=name):
                self.project = root / str(index)
                self.project.mkdir()
                target = self.project / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(external, target_is_directory=True)
                self.run_deploy("y\n" * len(FILES), expect_success=False)
                self.assertTrue(target.is_symlink())
                self.assertEqual(
                    {path.name: path.read_text(encoding="utf-8")
                     for path in external.iterdir()}, contents,
                )

    def test_dangling_symlinks_do_not_create_external_targets(self):
        root = self.project
        for index, name in enumerate(DIRECTORIES + FILES):
            with self.subTest(path=name):
                self.project = root / str(index)
                self.project.mkdir()
                external = root.parent / f"missing-{index}"
                target = self.project / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(external)
                self.run_deploy("y\n" * len(FILES), expect_success=False)
                self.assertTrue(target.is_symlink())
                self.assertFalse(external.exists())

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

    def test_absolute_script_path_scaffolds_working_directory(self):
        script_directory = self.project.parent / "script folder"
        script_directory.mkdir()
        script = script_directory / "deploy copy.sh"
        shutil.copyfile(SCRIPT, script)
        sentinel = self.write_existing(script.name, "keep unrelated file\n")

        result = subprocess.run(
            ["bash", str(script)], cwd=self.project, input="",
            text=True, capture_output=True, timeout=10,
        )

        self.assertEqual(result.returncode, 0, "Scaffolder failed")
        self.assertFalse(script.exists())
        self.assertEqual(sentinel.read_text(encoding="utf-8"),
                         "keep unrelated file\n")
        self.assertEqual(list(script_directory.iterdir()), [])
        for name in FILES:
            self.assertTrue((self.project / name).is_file(), name)

    def test_file_blocking_required_directory_is_preserved(self):
        target = self.write_existing("docs", "keep existing file\n")
        script = self.project / "deploy copy.sh"
        shutil.copyfile(SCRIPT, script)
        result = subprocess.run(
            ["bash", script.name], cwd=self.project, input="",
            text=True, capture_output=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_text(encoding="utf-8"), "keep existing file\n")
        self.assertTrue(script.is_file())
        self.assertFalse((self.project / FILES[0]).exists())

    def test_directory_blocking_generated_file_is_preserved(self):
        root = self.project
        for index, name in enumerate(FILES):
            with self.subTest(path=name):
                self.project = root / str(index)
                self.project.mkdir()
                target = self.project / name
                target.mkdir(parents=True)
                sentinel = target / "keep.txt"
                sentinel.write_text("keep\n", encoding="utf-8")
                script = self.project / "deploy copy.sh"
                shutil.copyfile(SCRIPT, script)
                result = subprocess.run(
                    ["bash", script.name], cwd=self.project, input="",
                    text=True, capture_output=True, timeout=10,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep\n")
                self.assertTrue(script.is_file())
                self.assertNotIn("Project structure deployed successfully!",
                                 result.stdout)

    def test_rerun_preserves_nested_sentinels_when_accepting_overwrites(self):
        self.run_deploy()
        sentinels = [
            self.write_existing(f"{directory}/nested/keep.txt", "keep\n")
            for directory in DIRECTORIES
        ]
        self.run_deploy("y\n" * len(FILES))
        for sentinel in sentinels:
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep\n")

    def test_generated_gitignore_rules(self):
        self.run_deploy()
        subprocess.run(
            ["git", "init", "--quiet"], cwd=self.project,
            check=True, capture_output=True, timeout=10,
        )
        cases = {
            ".gitignore": False,
            "docs/file-structure.md": False,
            "docs/backend/guide.md": False,
            "docs/_build/index.html": True,
            "Example$py.class": True,
            "Example.class": False,
            "__pycache__/example.pyc": True,
            ".env": True,
        }
        for name, ignored in cases.items():
            with self.subTest(path=name):
                result = subprocess.run(
                    ["git", "-c", "core.excludesFile=", "check-ignore",
                     "--no-index", "--quiet", "--", name],
                    cwd=self.project, capture_output=True, timeout=10,
                )
                self.assertEqual(result.returncode, 0 if ignored else 1)

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

    def test_empty_existing_files_are_preserved_by_default(self):
        targets = [self.write_existing(name, "") for name in FILES]
        self.run_deploy("\n" * len(FILES))
        for target in targets:
            with self.subTest(path=target.relative_to(self.project)):
                self.assertTrue(target.is_file())
                self.assertEqual(target.read_bytes(), b"")

    def test_unrecognized_answers_preserve_existing_file(self):
        root = self.project
        for index, answer in enumerate(("yes\n", "y extra\n", "true\n", "1\n")):
            with self.subTest(answer=answer):
                self.project = root / str(index)
                self.project.mkdir()
                target = self.write_existing(FILES[0], "keep\n")
                self.run_deploy(answer)
                self.assertEqual(target.read_text(encoding="utf-8"), "keep\n")
                self.assertTrue((self.project / FILES[-1]).is_file())

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

    def test_eof_after_approved_overwrite_preserves_remaining_files(self):
        targets = [self.write_existing(name, "keep\n") for name in FILES]
        self.run_deploy("y\n")
        self.assertTrue(targets[0].read_text(encoding="utf-8").startswith(
            "# Copilot Instructions\n"))
        for target in targets[1:]:
            with self.subTest(path=target.relative_to(self.project)):
                self.assertEqual(target.read_text(encoding="utf-8"), "keep\n")
