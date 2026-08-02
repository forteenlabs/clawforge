from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from clawforge.state import (
    LocalState,
    StateError,
    collect_local_state,
    format_state_report,
)


def run_git(repository: Path, *arguments: str) -> str:
    """Run Git inside a test repository."""

    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )

    return completed.stdout.strip()


def create_repository(repository: Path) -> None:
    """Create a minimal committed Git repository for testing."""

    run_git(repository, "init", "-b", "main")
    run_git(repository, "config", "user.name", "ClawForge Test")
    run_git(repository, "config", "user.email", "test@clawforge.local")
    run_git(repository, "config", "core.autocrlf", "false")

    readme = repository / "README.md"
    readme.write_text("# Test Repository\n", encoding="utf-8")

    run_git(repository, "add", "README.md")
    run_git(repository, "commit", "-m", "Create test repository")


class CollectLocalStateTests(unittest.TestCase):
    def test_collects_clean_repository_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_repository(repository)

            state = collect_local_state(repository)

            self.assertEqual(state.repository_root, repository.resolve())
            self.assertEqual(state.branch, "main")
            self.assertTrue(state.commit)
            self.assertEqual(state.working_tree, "clean")
            self.assertEqual(state.tracked_changes, ())
            self.assertEqual(state.untracked_files, ())

    def test_detects_tracked_and_untracked_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_repository(repository)

            readme = repository / "README.md"
            readme.write_text(
                "# Changed Test Repository\n",
                encoding="utf-8",
            )

            untracked_file = repository / "notes.txt"
            untracked_file.write_text(
                "Untracked evidence\n",
                encoding="utf-8",
            )

            state = collect_local_state(repository)

            self.assertEqual(state.working_tree, "modified")
            self.assertTrue(
                any("README.md" in item for item in state.tracked_changes)
            )
            self.assertEqual(state.untracked_files, ("notes.txt",))

    def test_raises_state_error_outside_git_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            location = Path(temporary_directory)

            with self.assertRaises(StateError):
                collect_local_state(location)


class FormatStateReportTests(unittest.TestCase):
    def test_report_preserves_remote_uncertainty(self) -> None:
        state = LocalState(
            repository_root=Path("C:/example/clawforge"),
            branch="main",
            commit="abc1234",
            tracked_changes=(),
            untracked_files=(),
        )

        report = format_state_report(state)

        self.assertIn("Working tree: clean", report)
        self.assertIn("Remote state: not refreshed", report)


if __name__ == "__main__":
    unittest.main()