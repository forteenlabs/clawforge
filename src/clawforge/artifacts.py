from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


STABLE_ANCHORS = (
    "VISION.md",
    "BUILD_LOG.md",
    "SESSION_HANDOFF.md",
    "docs/ARCHITECTURE.md",
    "docs/GOVERNANCE.md",
    "docs/DECISIONS.md",
    "docs/ROADMAP.md",
    "docs/foundation/README.md",
)

_BUILD_LINK_PATTERN = re.compile(
    r"\[([^\]]+)\]\(([^)]+\.md)\)"
)

_ADR_HEADING_PATTERN = re.compile(
    r"^##\s+(ADR-\d{4})\b.*$"
)

_ADR_STATUS_PATTERN = re.compile(
    r"^\*\*Status:\*\*\s*(.+?)\s*$"
)


@dataclass(frozen=True)
class ArtifactRecord:
    """One governed artifact discovered in the repository."""

    category: str
    identifier: str
    relative_path: str
    status: str
    source: str


@dataclass(frozen=True)
class ArtifactInventory:
    """Observable evidence about governed ClawForge artifacts."""

    anchors: tuple[ArtifactRecord, ...]
    builds: tuple[ArtifactRecord, ...]
    foundation: tuple[ArtifactRecord, ...]
    decisions: tuple[ArtifactRecord, ...]
    issues: tuple[str, ...]

    @property
    def records(self) -> tuple[ArtifactRecord, ...]:
        """Return all discovered artifact records."""

        return (
            self.anchors
            + self.builds
            + self.foundation
            + self.decisions
        )

    @property
    def missing_count(self) -> int:
        """Return the number of expected artifacts not found."""

        return sum(
            record.status == "missing"
            for record in self.records
        )


def _artifact_record(
    repository_root: Path,
    *,
    category: str,
    identifier: str,
    relative_path: str,
    source: str,
) -> ArtifactRecord:
    """Create a record showing whether an artifact exists."""

    artifact_path = repository_root / relative_path

    status = (
        "present"
        if artifact_path.is_file()
        else "missing"
    )

    return ArtifactRecord(
        category=category,
        identifier=identifier,
        relative_path=relative_path,
        status=status,
        source=source,
    )


def _read_text(
    path: Path,
    *,
    relative_path: str,
    issues: list[str],
) -> str | None:
    """Read one UTF-8 document while preserving failure evidence."""

    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except UnicodeDecodeError as exc:
        issues.append(
            f"{relative_path} is not valid UTF-8: {exc}"
        )
    except OSError as exc:
        issues.append(
            f"{relative_path} could not be read: {exc}"
        )

    return None


def _safe_repository_path(
    target: str,
) -> str | None:
    """Return a safe normalized repository-relative Markdown path."""

    normalized = target.split("#", 1)[0].replace("\\", "/")
    candidate = PurePosixPath(normalized)

    if candidate.is_absolute():
        return None

    if not candidate.parts:
        return None

    if ".." in candidate.parts:
        return None

    return candidate.as_posix()


def _discover_builds(
    repository_root: Path,
    issues: list[str],
) -> tuple[ArtifactRecord, ...]:
    """Discover build records linked by BUILD_LOG.md."""

    relative_index = "BUILD_LOG.md"
    build_log = repository_root / relative_index

    text = _read_text(
        build_log,
        relative_path=relative_index,
        issues=issues,
    )

    if text is None:
        return ()

    records: list[ArtifactRecord] = []
    seen_paths: set[str] = set()
    seen_identifiers: set[str] = set()

    for match in _BUILD_LINK_PATTERN.finditer(text):
        identifier = match.group(1).strip()
        target = match.group(2).strip()
        relative_path = _safe_repository_path(target)

        if relative_path is None:
            issues.append(
                f"BUILD_LOG.md contains an unsafe Markdown path: "
                f"{target}"
            )
            continue

        path_parts = PurePosixPath(relative_path).parts

        if not path_parts or path_parts[0] != "builds":
            continue

        if relative_path in seen_paths:
            issues.append(
                f"BUILD_LOG.md contains a duplicate build path: "
                f"{relative_path}"
            )
            continue

        if identifier in seen_identifiers:
            issues.append(
                f"BUILD_LOG.md contains a duplicate build "
                f"identifier: {identifier}"
            )
            continue

        seen_paths.add(relative_path)
        seen_identifiers.add(identifier)

        records.append(
            _artifact_record(
                repository_root,
                category="build",
                identifier=identifier,
                relative_path=relative_path,
                source=relative_index,
            )
        )

    if not records:
        issues.append(
            "BUILD_LOG.md contains no discoverable build records."
        )

    return tuple(records)


def _discover_foundation(
    repository_root: Path,
    issues: list[str],
) -> tuple[ArtifactRecord, ...]:
    """Discover First Principle documents by governed filename."""

    foundation_directory = (
        repository_root / "docs" / "foundation"
    )

    if not foundation_directory.is_dir():
        issues.append(
            "docs/foundation/ is unavailable."
        )
        return ()

    principle_files = sorted(
        foundation_directory.glob("FP-*.md")
    )

    if not principle_files:
        issues.append(
            "No First Principle files matching "
            "docs/foundation/FP-*.md were discovered."
        )
        return ()

    records = []

    for principle_file in principle_files:
        relative_path = principle_file.relative_to(
            repository_root
        ).as_posix()

        records.append(
            ArtifactRecord(
                category="foundation",
                identifier=principle_file.stem,
                relative_path=relative_path,
                status="present",
                source="docs/foundation/FP-*.md",
            )
        )

    return tuple(records)


def _finalize_decision_entry(
    repository_root: Path,
    *,
    identifier: str,
    statuses: list[str],
    seen_identifiers: set[str],
    records: list[ArtifactRecord],
    issues: list[str],
) -> None:
    """Validate and preserve one ADR index entry."""

    if identifier in seen_identifiers:
        issues.append(
            f"docs/DECISIONS.md contains a duplicate ADR "
            f"identifier: {identifier}"
        )
        return

    seen_identifiers.add(identifier)

    if not statuses:
        issues.append(
            f"{identifier} has no status in docs/DECISIONS.md."
        )
        return

    normalized_statuses = {
        status.strip().lower()
        for status in statuses
    }

    if len(normalized_statuses) > 1:
        issues.append(
            f"{identifier} has contradictory statuses in "
            f"docs/DECISIONS.md: {', '.join(statuses)}"
        )
        return

    status = statuses[0].strip()

    if status.lower() not in {"accepted", "frozen"}:
        return

    relative_path = f"docs/decisions/{identifier}.md"

    records.append(
        _artifact_record(
            repository_root,
            category="decision",
            identifier=identifier,
            relative_path=relative_path,
            source="docs/DECISIONS.md",
        )
    )


def _discover_decisions(
    repository_root: Path,
    issues: list[str],
) -> tuple[ArtifactRecord, ...]:
    """Discover Accepted and Frozen ADRs from their index."""

    relative_index = "docs/DECISIONS.md"
    decision_index = repository_root / relative_index

    text = _read_text(
        decision_index,
        relative_path=relative_index,
        issues=issues,
    )

    if text is None:
        return ()

    records: list[ArtifactRecord] = []
    seen_identifiers: set[str] = set()

    current_identifier: str | None = None
    current_statuses: list[str] = []

    for line in text.splitlines():
        heading_match = _ADR_HEADING_PATTERN.match(line)

        if heading_match is not None:
            if current_identifier is not None:
                _finalize_decision_entry(
                    repository_root,
                    identifier=current_identifier,
                    statuses=current_statuses,
                    seen_identifiers=seen_identifiers,
                    records=records,
                    issues=issues,
                )

            current_identifier = heading_match.group(1)
            current_statuses = []
            continue

        if current_identifier is None:
            continue

        status_match = _ADR_STATUS_PATTERN.match(line)

        if status_match is not None:
            current_statuses.append(
                status_match.group(1).strip()
            )

    if current_identifier is not None:
        _finalize_decision_entry(
            repository_root,
            identifier=current_identifier,
            statuses=current_statuses,
            seen_identifiers=seen_identifiers,
            records=records,
            issues=issues,
        )

    if not records:
        issues.append(
            "docs/DECISIONS.md contains no Accepted or Frozen "
            "ADR records."
        )

    return tuple(records)


def discover_artifacts(
    repository_root: Path,
) -> ArtifactInventory:
    """Discover stable and governed ClawForge artifacts."""

    root = repository_root.resolve()
    issues: list[str] = []

    anchors = tuple(
        _artifact_record(
            root,
            category="anchor",
            identifier=relative_path,
            relative_path=relative_path,
            source="stable anchor definition",
        )
        for relative_path in STABLE_ANCHORS
    )

    builds = _discover_builds(root, issues)
    foundation = _discover_foundation(root, issues)
    decisions = _discover_decisions(root, issues)

    return ArtifactInventory(
        anchors=anchors,
        builds=builds,
        foundation=foundation,
        decisions=decisions,
        issues=tuple(issues),
    )