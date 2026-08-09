from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from clawforge.artifacts import (
    ArtifactInventory,
    ArtifactRecord,
)
from clawforge.build_state import (
    BuildDeclaration,
    BuildStateEvidence,
)
from clawforge.known_good import KnownGoodEvidence

from clawforge.state import (
    LocalState,
    RemoteState,
    StateError,
    collect_local_state,
    collect_remote_state,
    format_state_report,
)


def run_git(location: Path, *arguments: str) -> str:
    """Run Git in a test location."""

    completed = subprocess.run(
        ["git", *arguments],
        cwd=location,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )

    return completed.stdout.strip()


def configure_identity(repository: Path) -> None:
    """Configure a local identity for test commits."""

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


def create_repository(repository: Path) -> None:
    """Create a minimal committed Git repository."""

    run_git(repository, "init", "-b", "main")
    configure_identity(repository)

    commit_file(
        repository,
        "README.md",
        "# Test Repository\n",
        "Create test repository",
    )


def commit_file(
    repository: Path,
    filename: str,
    content: str,
    message: str,
) -> None:
    """Write and commit one file in a test repository."""

    file_path = repository / filename
    file_path.write_text(content, encoding="utf-8")

    run_git(repository, "add", filename)
    run_git(repository, "commit", "-m", message)


def create_remote_pair(root: Path) -> tuple[Path, Path]:
    """Create a local repository with a configured bare remote."""

    remote = root / "remote.git"
    remote.mkdir()
    run_git(remote, "init", "--bare")

    local = root / "local"
    local.mkdir()
    create_repository(local)

    run_git(local, "remote", "add", "origin", str(remote))
    run_git(local, "push", "-u", "origin", "main")

    run_git(
        remote,
        "symbolic-ref",
        "HEAD",
        "refs/heads/main",
    )

    return local, remote


def create_peer(root: Path, remote: Path) -> Path:
    """Create a second repository connected to the test remote."""

    peer = root / "peer"
    peer.mkdir()

    run_git(peer, "init", "-b", "main")
    configure_identity(peer)
    run_git(peer, "remote", "add", "origin", str(remote))
    run_git(peer, "fetch", "origin", "main")
    run_git(peer, "checkout", "-B", "main", "origin/main")

    return peer


class CollectLocalStateTests(unittest.TestCase):
    def test_collects_clean_repository_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_repository(repository)

            state = collect_local_state(repository)

            self.assertEqual(
                state.repository_root,
                repository.resolve(),
            )
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
                any(
                    "README.md" in item
                    for item in state.tracked_changes
                )
            )
            self.assertEqual(
                state.untracked_files,
                ("notes.txt",),
            )

    def test_raises_state_error_outside_git_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            location = Path(temporary_directory)

            with self.assertRaises(StateError):
                collect_local_state(location)


    def test_reports_git_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            location = Path(temporary_directory)

            with patch(
                "clawforge.state.subprocess.run",
                side_effect=FileNotFoundError,
            ):
                with self.assertRaisesRegex(
                    StateError,
                    "Git is not available on PATH",
                ):
                    collect_local_state(location)


class CollectRemoteStateTests(unittest.TestCase):
    def test_does_not_refresh_without_explicit_request(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_repository(repository)

            local_state = collect_local_state(repository)
            remote_state = collect_remote_state(local_state)

            self.assertEqual(
                remote_state,
                RemoteState(status="not refreshed"),
            )

    def test_reports_no_upstream_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_repository(repository)

            local_state = collect_local_state(repository)
            remote_state = collect_remote_state(
                local_state,
                refresh=True,
            )

            self.assertEqual(
                remote_state.status,
                "no upstream configured",
            )

    def test_reports_unavailable_when_refresh_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            local, _ = create_remote_pair(root)

            missing_remote = root / "missing.git"
            run_git(
                local,
                "remote",
                "set-url",
                "origin",
                str(missing_remote),
            )

            local_state = collect_local_state(local)
            remote_state = collect_remote_state(
                local_state,
                refresh=True,
            )

            self.assertEqual(remote_state.status, "unavailable")

    def test_reports_synchronized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            local, _ = create_remote_pair(root)

            local_state = collect_local_state(local)
            remote_state = collect_remote_state(
                local_state,
                refresh=True,
            )

            self.assertEqual(remote_state.status, "synchronized")
            self.assertEqual(remote_state.upstream, "origin/main")
            self.assertEqual(remote_state.ahead, 0)
            self.assertEqual(remote_state.behind, 0)

    def test_reports_locally_ahead(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            local, _ = create_remote_pair(root)

            commit_file(
                local,
                "local.txt",
                "Local change\n",
                "Create local change",
            )

            local_state = collect_local_state(local)
            remote_state = collect_remote_state(
                local_state,
                refresh=True,
            )

            self.assertEqual(remote_state.status, "locally ahead")
            self.assertEqual(remote_state.ahead, 1)
            self.assertEqual(remote_state.behind, 0)

    def test_reports_locally_behind(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            local, remote = create_remote_pair(root)
            peer = create_peer(root, remote)

            commit_file(
                peer,
                "peer.txt",
                "Remote change\n",
                "Create remote change",
            )
            run_git(peer, "push", "origin", "main")

            local_state = collect_local_state(local)
            remote_state = collect_remote_state(
                local_state,
                refresh=True,
            )

            self.assertEqual(remote_state.status, "locally behind")
            self.assertEqual(remote_state.ahead, 0)
            self.assertEqual(remote_state.behind, 1)

    def test_reports_diverged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            local, remote = create_remote_pair(root)
            peer = create_peer(root, remote)

            commit_file(
                local,
                "local.txt",
                "Local change\n",
                "Create local change",
            )

            commit_file(
                peer,
                "peer.txt",
                "Remote change\n",
                "Create remote change",
            )
            run_git(peer, "push", "origin", "main")

            local_state = collect_local_state(local)
            remote_state = collect_remote_state(
                local_state,
                refresh=True,
            )

            self.assertEqual(remote_state.status, "diverged")
            self.assertEqual(remote_state.ahead, 1)
            self.assertEqual(remote_state.behind, 1)


class FormatStateReportTests(unittest.TestCase):
    def test_report_preserves_remote_uncertainty(self) -> None:
        local_state = LocalState(
            repository_root=Path("C:/example/clawforge"),
            branch="main",
            commit="abc1234",
            tracked_changes=(),
            untracked_files=(),
        )

        report = format_state_report(local_state)

        self.assertIn("Working tree: clean", report)
        self.assertIn("Remote state: not refreshed", report)

    def test_report_includes_remote_relationship(self) -> None:
        local_state = LocalState(
            repository_root=Path("C:/example/clawforge"),
            branch="main",
            commit="abc1234",
            tracked_changes=(),
            untracked_files=(),
        )

        remote_state = RemoteState(
            status="locally ahead",
            upstream="origin/main",
            ahead=2,
            behind=0,
        )

        report = format_state_report(
            local_state,
            remote_state,
        )

        self.assertIn("Remote state: locally ahead", report)
        self.assertIn("Upstream: origin/main", report)
        self.assertIn("Ahead: 2", report)
        self.assertIn("Behind: 0", report)


    def test_report_includes_complete_artifact_inventory(
        self,
    ) -> None:
        local_state = LocalState(
            repository_root=Path("C:/example/clawforge"),
            branch="main",
            commit="abc1234",
            tracked_changes=(),
            untracked_files=(),
        )

        inventory = ArtifactInventory(
            anchors=(
                ArtifactRecord(
                    category="anchor",
                    identifier="VISION.md",
                    relative_path="VISION.md",
                    status="present",
                    source="stable anchor definition",
                ),
            ),
            builds=(),
            foundation=(),
            decisions=(),
            issues=(),
        )

        report = format_state_report(
            local_state,
            artifact_inventory=inventory,
        )

        self.assertIn("Artifact inventory: complete", report)
        self.assertIn("Stable anchors: 1", report)
        self.assertIn("Missing artifacts: 0", report)
        self.assertIn("Discovery issues: 0", report)

    def test_report_preserves_incomplete_artifact_evidence(
        self,
    ) -> None:
        local_state = LocalState(
            repository_root=Path("C:/example/clawforge"),
            branch="main",
            commit="abc1234",
            tracked_changes=(),
            untracked_files=(),
        )

        inventory = ArtifactInventory(
            anchors=(
                ArtifactRecord(
                    category="anchor",
                    identifier="VISION.md",
                    relative_path="VISION.md",
                    status="missing",
                    source="stable anchor definition",
                ),
            ),
            builds=(),
            foundation=(),
            decisions=(),
            issues=(
                "BUILD_LOG.md could not be interpreted.",
            ),
        )

        report = format_state_report(
            local_state,
            artifact_inventory=inventory,
        )

        self.assertIn("Artifact inventory: incomplete", report)
        self.assertIn("Missing artifacts: 1", report)
        self.assertIn("[anchor] VISION.md", report)
        self.assertIn(
            "BUILD_LOG.md could not be interpreted.",
            report,
        )


    def test_report_includes_consistent_build_state(
        self,
    ) -> None:
        local_state = LocalState(
            repository_root=Path("C:/example/clawforge"),
            branch="main",
            commit="abc1234",
            tracked_changes=(),
            untracked_files=(),
        )

        build_state = BuildStateEvidence(
            completed_builds=(
                BuildDeclaration(
                    identifier="0.0.1",
                    title="Foundation",
                    line=11,
                    relative_path="builds/0.0.1-foundation.md",
                ),
            ),
            current_builds=(
                BuildDeclaration(
                    identifier="0.0.2",
                    title="State",
                    line=21,
                ),
            ),
            current_statuses=("Active Discovery",),
            known_good_states=("abc1234",),
            no_active_build_declared=False,
            issues=(),
        )

        report = format_state_report(
            local_state,
            build_state=build_state,
        )

        self.assertIn("Build state: consistent", report)
        self.assertIn("Completed builds: 1", report)
        self.assertIn("Current build: 0.0.2 - State", report)
        self.assertIn("Current status: Active Discovery", report)
        self.assertIn("Known Good State: abc1234", report)
        self.assertIn("Build-state issues: 0", report)

    def test_report_preserves_build_state_conflicts(
        self,
    ) -> None:
        local_state = LocalState(
            repository_root=Path("C:/example/clawforge"),
            branch="main",
            commit="abc1234",
            tracked_changes=(),
            untracked_files=(),
        )

        issue = (
            "BUILD_LOG.md declares Build 0.0.2 as both current "
            "and completed."
        )

        build_state = BuildStateEvidence(
            completed_builds=(
                BuildDeclaration(
                    identifier="0.0.2",
                    title="State",
                    line=11,
                    relative_path="builds/0.0.2-state.md",
                ),
            ),
            current_builds=(
                BuildDeclaration(
                    identifier="0.0.2",
                    title="State",
                    line=21,
                ),
            ),
            current_statuses=(
                "Active Discovery",
                "Build 0.0.1 Finalized",
            ),
            known_good_states=("abc1234",),
            no_active_build_declared=False,
            issues=(issue,),
        )

        report = format_state_report(
            local_state,
            build_state=build_state,
        )

        self.assertIn("Build state: inconsistent", report)
        self.assertIn(
            "Current status: ambiguous (2 declarations)",
            report,
        )
        self.assertIn("Build-state issues: 1", report)
        self.assertIn(issue, report)


    def test_report_includes_known_good_ancestor_evidence(
        self,
    ) -> None:
        local_state = LocalState(
            repository_root=Path("C:/example/clawforge"),
            branch="main",
            commit="def5678",
            tracked_changes=(),
            untracked_files=(),
        )

        known_good = KnownGoodEvidence(
            declared_commit="abc1234",
            resolved_commit=(
                "abc1234567890abc1234567890abc1234567890"
            ),
            status="ancestor",
        )

        report = format_state_report(
            local_state,
            known_good=known_good,
        )

        self.assertIn(
            "Known Good verification: ancestor",
            report,
        )
        self.assertIn(
            "Declared Known Good commit: abc1234",
            report,
        )
        self.assertIn(
            "Known Good commit exists: yes",
            report,
        )
        self.assertIn(
            "Resolved Known Good commit: "
            "abc1234567890abc1234567890abc1234567890",
            report,
        )

    def test_report_preserves_missing_known_good_evidence(
        self,
    ) -> None:
        local_state = LocalState(
            repository_root=Path("C:/example/clawforge"),
            branch="main",
            commit="def5678",
            tracked_changes=(),
            untracked_files=(),
        )

        detail = (
            "The declared Known Good State could not be "
            "resolved as a commit."
        )

        known_good = KnownGoodEvidence(
            declared_commit="deadbee",
            resolved_commit=None,
            status="missing",
            detail=detail,
        )

        report = format_state_report(
            local_state,
            known_good=known_good,
        )

        self.assertIn(
            "Known Good verification: missing",
            report,
        )
        self.assertIn(
            "Declared Known Good commit: deadbee",
            report,
        )
        self.assertIn(
            "Known Good commit exists: no",
            report,
        )
        self.assertIn(detail, report)


if __name__ == "__main__":
    unittest.main()