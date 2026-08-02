from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_COMPLETED_BUILD_PATTERN = re.compile(
    r"^\s*-\s+\[Build\s+"
    r"(\d+\.\d+\.\d+)\s+[\u2014\u2013-]\s+"
    r"([^\]]+)"
    r"\]\(([^)]+)\)\s*$"
)

_CURRENT_BUILD_PATTERN = re.compile(
    r"^###\s+Build\s+"
    r"(\d+\.\d+\.\d+)\s+[\u2014\u2013-]\s+"
    r"(.+?)\s*$"
)

_STATUS_PATTERN = re.compile(
    r"^Status:\s*(.+?)\s*$"
)

_KNOWN_GOOD_PATTERN = re.compile(
    r"^Current Known Good State:\s*"
    r"`?([0-9a-fA-F]{7,40})`?\s*$"
)

_BUILD_REFERENCE_PATTERN = re.compile(
    r"\bBuild\s+(\d+\.\d+\.\d+)\b",
    re.IGNORECASE,
)

_NO_ACTIVE_BUILD_PATTERN = re.compile(
    r"\bno active build\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class BuildDeclaration:
    """One build declaration found in BUILD_LOG.md."""

    identifier: str
    title: str
    line: int
    relative_path: str | None = None


@dataclass(frozen=True)
class BuildStateEvidence:
    """Observable build-state declarations and unresolved issues."""

    completed_builds: tuple[BuildDeclaration, ...]
    current_builds: tuple[BuildDeclaration, ...]
    current_statuses: tuple[str, ...]
    known_good_states: tuple[str, ...]
    no_active_build_declared: bool
    issues: tuple[str, ...]

    @property
    def current_build(self) -> BuildDeclaration | None:
        """Return the current build only when exactly one is declared."""

        if len(self.current_builds) == 1:
            return self.current_builds[0]

        return None

    @property
    def current_status(self) -> str | None:
        """Return the current status only when exactly one is declared."""

        if len(self.current_statuses) == 1:
            return self.current_statuses[0]

        return None

    @property
    def known_good_state(self) -> str | None:
        """Return Known Good State only when exactly one is declared."""

        if len(self.known_good_states) == 1:
            return self.known_good_states[0]

        return None

    @property
    def is_consistent(self) -> bool:
        """Return whether no declaration issues were observed."""

        return not self.issues


def _section_lines(
    lines: tuple[str, ...],
    heading: str,
    issues: list[str],
) -> tuple[tuple[int, str], ...]:
    """Return numbered lines belonging to one level-two section."""

    matches = tuple(
        index
        for index, line in enumerate(lines)
        if line.strip() == heading
    )

    if not matches:
        issues.append(
            f"BUILD_LOG.md is missing the {heading} section."
        )
        return ()

    if len(matches) > 1:
        issues.append(
            f"BUILD_LOG.md contains multiple {heading} sections."
        )

    start = matches[0] + 1
    end = len(lines)

    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break

    return tuple(
        (index + 1, lines[index])
        for index in range(start, end)
    )


def _empty_evidence(
    issues: list[str],
) -> BuildStateEvidence:
    """Return build-state evidence containing only failure details."""

    return BuildStateEvidence(
        completed_builds=(),
        current_builds=(),
        current_statuses=(),
        known_good_states=(),
        no_active_build_declared=False,
        issues=tuple(issues),
    )


def inspect_build_state(
    repository_root: Path,
) -> BuildStateEvidence:
    """Interpret authoritative declarations in BUILD_LOG.md."""

    build_log = repository_root.resolve() / "BUILD_LOG.md"
    issues: list[str] = []

    try:
        text = build_log.read_text(encoding="utf-8")
    except FileNotFoundError:
        issues.append("BUILD_LOG.md could not be found.")
        return _empty_evidence(issues)
    except UnicodeDecodeError as exc:
        issues.append(
            f"BUILD_LOG.md is not valid UTF-8: {exc}"
        )
        return _empty_evidence(issues)
    except OSError as exc:
        issues.append(
            f"BUILD_LOG.md could not be read: {exc}"
        )
        return _empty_evidence(issues)

    lines = tuple(text.splitlines())

    completed_section = _section_lines(
        lines,
        "## Completed Builds",
        issues,
    )
    current_section = _section_lines(
        lines,
        "## Current Build",
        issues,
    )

    completed_builds: list[BuildDeclaration] = []
    completed_identifiers: set[str] = set()

    for line_number, line in completed_section:
        match = _COMPLETED_BUILD_PATTERN.match(line)

        if match is None:
            if line.lstrip().startswith("-") and "Build" in line:
                issues.append(
                    "BUILD_LOG.md contains a malformed completed-build "
                    f"declaration at line {line_number}."
                )
            continue

        identifier = match.group(1)
        title = match.group(2).strip()
        relative_path = match.group(3).strip()

        if identifier in completed_identifiers:
            issues.append(
                "BUILD_LOG.md contains duplicate completed-build "
                f"declarations for Build {identifier}."
            )

        completed_identifiers.add(identifier)

        completed_builds.append(
            BuildDeclaration(
                identifier=identifier,
                title=title,
                line=line_number,
                relative_path=relative_path,
            )
        )

    current_builds: list[BuildDeclaration] = []
    current_statuses: list[str] = []
    no_active_build_declared = False

    for line_number, line in current_section:
        stripped = line.strip()

        build_match = _CURRENT_BUILD_PATTERN.match(stripped)

        if build_match is not None:
            current_builds.append(
                BuildDeclaration(
                    identifier=build_match.group(1),
                    title=build_match.group(2).strip(),
                    line=line_number,
                )
            )
            continue

        status_match = _STATUS_PATTERN.match(stripped)

        if status_match is not None:
            current_statuses.append(
                status_match.group(1).strip()
            )

        if _NO_ACTIVE_BUILD_PATTERN.search(stripped):
            no_active_build_declared = True

    known_good_states: list[str] = []

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        if not stripped.startswith("Current Known Good State:"):
            continue

        match = _KNOWN_GOOD_PATTERN.match(stripped)

        if match is None:
            issues.append(
                "BUILD_LOG.md contains a malformed Current Known Good "
                f"State declaration at line {line_number}."
            )
            continue

        known_good_states.append(match.group(1))

    if len(current_builds) > 1:
        identifiers = ", ".join(
            build.identifier for build in current_builds
        )
        issues.append(
            "BUILD_LOG.md contains multiple current-build "
            f"declarations: {identifiers}."
        )

    if current_builds and no_active_build_declared:
        issues.append(
            "BUILD_LOG.md declares both a current build and no active "
            "build."
        )

    if not current_builds and not no_active_build_declared:
        issues.append(
            "BUILD_LOG.md does not clearly declare a current build or "
            "no active build."
        )

    if current_builds and not current_statuses:
        issues.append(
            "BUILD_LOG.md declares a current build without a status."
        )

    if len(current_statuses) > 1:
        issues.append(
            "BUILD_LOG.md current-build section contains multiple "
            "status declarations: "
            + "; ".join(current_statuses)
            + "."
        )

    current_identifiers = {
        build.identifier for build in current_builds
    }

    for identifier in sorted(
        current_identifiers.intersection(completed_identifiers)
    ):
        issues.append(
            f"BUILD_LOG.md declares Build {identifier} as both current "
            "and completed."
        )

    for status in current_statuses:
        for referenced_identifier in _BUILD_REFERENCE_PATTERN.findall(
            status
        ):
            if (
                current_identifiers
                and referenced_identifier not in current_identifiers
            ):
                issues.append(
                    "BUILD_LOG.md status references Build "
                    f"{referenced_identifier} while the current build "
                    "declaration identifies "
                    + ", ".join(sorted(current_identifiers))
                    + "."
                )

    if not known_good_states:
        issues.append(
            "BUILD_LOG.md does not declare a Current Known Good State."
        )

    if len(known_good_states) > 1:
        issues.append(
            "BUILD_LOG.md contains multiple Current Known Good State "
            "declarations: "
            + ", ".join(known_good_states)
            + "."
        )

    return BuildStateEvidence(
        completed_builds=tuple(completed_builds),
        current_builds=tuple(current_builds),
        current_statuses=tuple(current_statuses),
        known_good_states=tuple(known_good_states),
        no_active_build_declared=no_active_build_declared,
        issues=tuple(issues),
    )
