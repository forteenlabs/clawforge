from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from clawforge.known_good import inspect_known_good


def run_git(
    repository: Path,
    *arguments: str,
) -> str:
    """Run Git successfully in a test repository."""

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


def commit_file(
    repository: Path,
    filename: str,
    content: str,
    message: str,
) -> str:
    """Create one committed file and return the commit hash."""

    path = repository / filename
    path.write_text(content, encoding="utf-8")

    run_git(repository, "add", filename)
    run_git(repository, "commit", "-m", message)

    return run_git(repository, "rev-parse", "HEAD")


def create_repository(repository: Path) -> str:
    """Create a minimal repository and return its first commit."""

    run_git(repository, "init", "-b", "main")
    run_git(
        repository,
        "config",
        "user.name",
        "ClawForge Test",
    )
    run_git(
        repository,
        "config",
        "user.email",
        "test@clawforge.local",
    )
    run_git(
        repository,
        "config",
        "core.autocrlf",
        "false",
    )

    return commit_file(
        repository,
        "README.md",
        "# Test Repository\n",
        "Create test repository",
    )


class KnownGoodTests(unittest.TestCase):
    def test_reports_no_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            evidence = inspect_known_good(
                Path(temporary_directory),
                None,
            )

            self.assertEqual(evidence.status, "not declared")
            self.assertIsNone(evidence.commit_exists)

    def test_reports_missing_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_repository(repository)

            evidence = inspect_known_good(
                repository,
                "deadbee",
            )

            self.assertEqual(evidence.status, "missing")
            self.assertFalse(evidence.commit_exists)

    def test_reports_declared_commit_as_current(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            first_commit = create_repository(repository)

            evidence = inspect_known_good(
                repository,
                first_commit[:7],
            )

            self.assertEqual(evidence.status, "current")
            self.assertTrue(evidence.commit_exists)
            self.assertEqual(
                evidence.resolved_commit,
                first_commit,
            )

    def test_reports_declared_commit_as_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            first_commit = create_repository(repository)

            commit_file(
                repository,
                "next.txt",
                "Next change\n",
                "Create next change",
            )

            evidence = inspect_known_good(
                repository,
                first_commit[:7],
            )

            self.assertEqual(evidence.status, "ancestor")
            self.assertTrue(evidence.commit_exists)

    def test_reports_declared_commit_not_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            first_commit = create_repository(repository)

            run_git(repository, "checkout", "--orphan", "unrelated")
            run_git(repository, "rm", "-rf", ".")

            commit_file(
                repository,
                "unrelated.txt",
                "Unrelated history\n",
                "Create unrelated history",
            )

            evidence = inspect_known_good(
                repository,
                first_commit[:7],
            )

            self.assertEqual(
                evidence.status,
                "not ancestor",
            )
            self.assertTrue(evidence.commit_exists)

    def test_reports_unavailable_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            evidence = inspect_known_good(
                Path(temporary_directory),
                "deadbee",
            )

            self.assertEqual(evidence.status, "unavailable")
            self.assertIsNotNone(evidence.detail)


if __name__ == "__main__":
    unittest.main()
