from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from clawforge.build_state import inspect_build_state


def write_build_log(
    repository: Path,
    content: str,
) -> None:
    """Write one BUILD_LOG.md test fixture."""

    (repository / "BUILD_LOG.md").write_text(
        content,
        encoding="utf-8",
    )


class BuildStateTests(unittest.TestCase):
    def test_reports_consistent_active_build(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)

            write_build_log(
                repository,
                """# Build Log

## Completed Builds

- [Build 0.0.1 \u2014 Foundation](builds/0.0.1-foundation.md)

## Current Build

### Build 0.0.2 \u2014 State

Status: Active Discovery

Current Known Good State: `abc1234`
""",
            )

            evidence = inspect_build_state(repository)

            self.assertTrue(evidence.is_consistent)
            self.assertEqual(
                tuple(
                    build.identifier
                    for build in evidence.completed_builds
                ),
                ("0.0.1",),
            )
            self.assertEqual(
                evidence.current_build.identifier,
                "0.0.2",
            )
            self.assertEqual(
                evidence.current_status,
                "Active Discovery",
            )
            self.assertEqual(
                evidence.known_good_state,
                "abc1234",
            )

    def test_reports_current_build_also_completed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)

            write_build_log(
                repository,
                """## Completed Builds

- [Build 0.0.2 \u2014 State](builds/0.0.2-state.md)

## Current Build

### Build 0.0.2 \u2014 State

Status: Active Discovery

Current Known Good State: `abc1234`
""",
            )

            evidence = inspect_build_state(repository)

            self.assertIn(
                "BUILD_LOG.md declares Build 0.0.2 as both "
                "current and completed.",
                evidence.issues,
            )

    def test_preserves_multiple_and_mismatched_statuses(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)

            write_build_log(
                repository,
                """## Completed Builds

- [Build 0.0.1 \u2014 Foundation](builds/0.0.1-foundation.md)

## Current Build

### Build 0.0.2 \u2014 State

Status: Active Discovery
Status: Build 0.0.1 Finalized

Current Known Good State: `abc1234`
""",
            )

            evidence = inspect_build_state(repository)

            self.assertIsNone(evidence.current_status)
            self.assertIn(
                "BUILD_LOG.md current-build section contains multiple "
                "status declarations: Active Discovery; "
                "Build 0.0.1 Finalized.",
                evidence.issues,
            )
            self.assertIn(
                "BUILD_LOG.md status references Build 0.0.1 while "
                "the current build declaration identifies 0.0.2.",
                evidence.issues,
            )

    def test_reports_duplicate_completed_builds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)

            write_build_log(
                repository,
                """## Completed Builds

- [Build 0.0.1 \u2014 Foundation](builds/0.0.1-foundation.md)
- [Build 0.0.1 \u2014 Foundation](builds/0.0.1-copy.md)

## Current Build

### Build 0.0.2 \u2014 State

Status: Active Discovery

Current Known Good State: `abc1234`
""",
            )

            evidence = inspect_build_state(repository)

            self.assertIn(
                "BUILD_LOG.md contains duplicate completed-build "
                "declarations for Build 0.0.1.",
                evidence.issues,
            )

    def test_preserves_multiple_current_builds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)

            write_build_log(
                repository,
                """## Completed Builds

- [Build 0.0.1 \u2014 Foundation](builds/0.0.1-foundation.md)

## Current Build

### Build 0.0.2 \u2014 State
### Build 0.0.3 \u2014 Future

Status: Active Discovery

Current Known Good State: `abc1234`
""",
            )

            evidence = inspect_build_state(repository)

            self.assertIsNone(evidence.current_build)
            self.assertIn(
                "BUILD_LOG.md contains multiple current-build "
                "declarations: 0.0.2, 0.0.3.",
                evidence.issues,
            )

    def test_accepts_explicit_no_active_build(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)

            write_build_log(
                repository,
                """## Completed Builds

- [Build 0.0.1 \u2014 Foundation](builds/0.0.1-foundation.md)

## Current Build

There is no active build.

Current Known Good State: `abc1234`
""",
            )

            evidence = inspect_build_state(repository)

            self.assertTrue(evidence.is_consistent)
            self.assertTrue(evidence.no_active_build_declared)
            self.assertIsNone(evidence.current_build)

    def test_reports_malformed_known_good_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)

            write_build_log(
                repository,
                """## Completed Builds

- [Build 0.0.1 \u2014 Foundation](builds/0.0.1-foundation.md)

## Current Build

### Build 0.0.2 \u2014 State

Status: Active Discovery

Current Known Good State: unknown
""",
            )

            evidence = inspect_build_state(repository)

            self.assertIn(
                "BUILD_LOG.md contains a malformed Current Known Good "
                "State declaration at line 11.",
                evidence.issues,
            )
            self.assertIsNone(evidence.known_good_state)

    def test_reports_missing_build_log(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            evidence = inspect_build_state(
                Path(temporary_directory)
            )

            self.assertEqual(
                evidence.issues,
                ("BUILD_LOG.md could not be found.",),
            )


if __name__ == "__main__":
    unittest.main()
