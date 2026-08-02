from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from clawforge.artifacts import (
    STABLE_ANCHORS,
    discover_artifacts,
)


def write_file(
    repository: Path,
    relative_path: str,
    content: str = "",
) -> None:
    """Create one UTF-8 test artifact."""

    path = repository / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_valid_artifact_repository(repository: Path) -> None:
    """Create a minimal repository with discoverable artifacts."""

    for relative_path in STABLE_ANCHORS:
        write_file(repository, relative_path)

    write_file(
        repository,
        "BUILD_LOG.md",
        "\n".join(
            [
                "# Build Log",
                "",
                "- [Build 0.0.1 — Foundation]"
                "(builds/0.0.1-foundation.md)",
                "- [Build 0.0.2 — State]"
                "(builds/0.0.2-state.md)",
                "",
            ]
        ),
    )

    write_file(
        repository,
        "builds/0.0.1-foundation.md",
        "# Build 0.0.1\n",
    )
    write_file(
        repository,
        "builds/0.0.2-state.md",
        "# Build 0.0.2\n",
    )

    write_file(
        repository,
        "docs/foundation/FP-000-purpose.md",
        "# FP-000\n",
    )
    write_file(
        repository,
        "docs/foundation/FP-001-continuity.md",
        "# FP-001\n",
    )

    write_file(
        repository,
        "docs/DECISIONS.md",
        "\n".join(
            [
                "# Decisions",
                "",
                "## ADR-0000 — ADR Process",
                "",
                "**Status:** Frozen",
                "",
                "## ADR-0001 — State",
                "",
                "**Status:** Accepted",
                "",
                "## ADR-0002 — Future",
                "",
                "**Status:** Proposed",
                "",
            ]
        ),
    )

    write_file(
        repository,
        "docs/decisions/ADR-0000.md",
        "# ADR-0000\n",
    )
    write_file(
        repository,
        "docs/decisions/ADR-0001.md",
        "# ADR-0001\n",
    )


class StableAnchorTests(unittest.TestCase):
    def test_reports_present_stable_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_valid_artifact_repository(repository)

            inventory = discover_artifacts(repository)

            self.assertEqual(
                len(inventory.anchors),
                len(STABLE_ANCHORS),
            )
            self.assertTrue(
                all(
                    record.status == "present"
                    for record in inventory.anchors
                )
            )

    def test_reports_missing_stable_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_valid_artifact_repository(repository)

            missing_path = repository / "VISION.md"
            missing_path.unlink()

            inventory = discover_artifacts(repository)

            vision_record = next(
                record
                for record in inventory.anchors
                if record.relative_path == "VISION.md"
            )

            self.assertEqual(vision_record.status, "missing")
            self.assertEqual(inventory.missing_count, 1)


class BuildDiscoveryTests(unittest.TestCase):
    def test_discovers_builds_from_build_log_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_valid_artifact_repository(repository)

            inventory = discover_artifacts(repository)

            self.assertEqual(
                tuple(
                    record.identifier
                    for record in inventory.builds
                ),
                (
                    "Build 0.0.1 — Foundation",
                    "Build 0.0.2 — State",
                ),
            )
            self.assertTrue(
                all(
                    record.status == "present"
                    for record in inventory.builds
                )
            )

    def test_reports_missing_linked_build(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_valid_artifact_repository(repository)

            missing_build = (
                repository / "builds" / "0.0.2-state.md"
            )
            missing_build.unlink()

            inventory = discover_artifacts(repository)

            state_build = next(
                record
                for record in inventory.builds
                if record.relative_path
                == "builds/0.0.2-state.md"
            )

            self.assertEqual(state_build.status, "missing")
            self.assertEqual(inventory.missing_count, 1)

    def test_rejects_unsafe_build_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_valid_artifact_repository(repository)

            write_file(
                repository,
                "BUILD_LOG.md",
                "\n".join(
                    [
                        "# Build Log",
                        "",
                        "- [Unsafe Build](../outside.md)",
                        "",
                    ]
                ),
            )

            inventory = discover_artifacts(repository)

            self.assertEqual(inventory.builds, ())
            self.assertTrue(
                any(
                    "unsafe Markdown path" in issue
                    for issue in inventory.issues
                )
            )


class FoundationDiscoveryTests(unittest.TestCase):
    def test_discovers_first_principles_by_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_valid_artifact_repository(repository)

            inventory = discover_artifacts(repository)

            self.assertEqual(
                tuple(
                    record.identifier
                    for record in inventory.foundation
                ),
                (
                    "FP-000-purpose",
                    "FP-001-continuity",
                ),
            )

    def test_reports_missing_foundation_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)

            inventory = discover_artifacts(repository)

            self.assertTrue(
                any(
                    "docs/foundation/ is unavailable" in issue
                    for issue in inventory.issues
                )
            )


class DecisionDiscoveryTests(unittest.TestCase):
    def test_discovers_only_accepted_and_frozen_decisions(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_valid_artifact_repository(repository)

            inventory = discover_artifacts(repository)

            self.assertEqual(
                tuple(
                    record.identifier
                    for record in inventory.decisions
                ),
                (
                    "ADR-0000",
                    "ADR-0001",
                ),
            )

    def test_reports_missing_accepted_decision_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_valid_artifact_repository(repository)

            decision_file = (
                repository
                / "docs"
                / "decisions"
                / "ADR-0001.md"
            )
            decision_file.unlink()

            inventory = discover_artifacts(repository)

            decision = next(
                record
                for record in inventory.decisions
                if record.identifier == "ADR-0001"
            )

            self.assertEqual(decision.status, "missing")
            self.assertEqual(inventory.missing_count, 1)

    def test_reports_contradictory_decision_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            create_valid_artifact_repository(repository)

            write_file(
                repository,
                "docs/DECISIONS.md",
                "\n".join(
                    [
                        "# Decisions",
                        "",
                        "## ADR-0001 — Contradictory",
                        "",
                        "**Status:** Accepted",
                        "**Status:** Frozen",
                        "",
                    ]
                ),
            )

            inventory = discover_artifacts(repository)

            self.assertEqual(inventory.decisions, ())
            self.assertTrue(
                any(
                    "contradictory statuses" in issue
                    for issue in inventory.issues
                )
            )


if __name__ == "__main__":
    unittest.main()