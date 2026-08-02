from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from clawforge.artifacts import (
    ArtifactInventory,
    discover_artifacts,
)
from clawforge.build_state import (
    BuildStateEvidence,
    inspect_build_state,
)
from clawforge.known_good import (
    KnownGoodEvidence,
    inspect_known_good,
)


class StateError(RuntimeError):
    """Raised when repository state evidence cannot be collected."""


@dataclass(frozen=True)
class LocalState:
    """Observable local evidence about a Git repository."""

    repository_root: Path
    branch: str
    commit: str
    tracked_changes: tuple[str, ...]
    untracked_files: tuple[str, ...]

    @property
    def working_tree(self) -> str:
        """Return a human-readable working-tree condition."""

        if self.tracked_changes or self.untracked_files:
            return "modified"

        return "clean"


@dataclass(frozen=True)
class RemoteState:
    """Observable evidence about the current branch and its upstream."""

    status: str
    upstream: str | None = None
    ahead: int | None = None
    behind: int | None = None
    detail: str | None = None


def _execute_git(
    *arguments: str,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    """Run Git and return its completed process."""

    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as exc:
        raise StateError("Git is not available on PATH.") from exc


def _run_git(*arguments: str, cwd: Path) -> str:
    """Run a successful Git command and return its standard output."""

    completed = _execute_git(*arguments, cwd=cwd)

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        command = " ".join(("git", *arguments))

        if not detail:
            detail = "Git returned no diagnostic information."

        raise StateError(f"{command} failed: {detail}")

    return completed.stdout.strip()


def collect_local_state(start: Path | None = None) -> LocalState:
    """Collect read-only local repository evidence."""

    start_path = (start or Path.cwd()).resolve()

    repository_root = Path(
        _run_git("rev-parse", "--show-toplevel", cwd=start_path)
    ).resolve()

    branch = _run_git("branch", "--show-current", cwd=repository_root)

    if not branch:
        branch = "(detached HEAD)"

    commit = _run_git(
        "rev-parse",
        "--short",
        "HEAD",
        cwd=repository_root,
    )

    status_output = _run_git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        cwd=repository_root,
    )

    status_lines = tuple(
        line for line in status_output.splitlines() if line
    )

    tracked_changes = tuple(
        line for line in status_lines if not line.startswith("?? ")
    )

    untracked_files = tuple(
        line[3:] for line in status_lines if line.startswith("?? ")
    )

    return LocalState(
        repository_root=repository_root,
        branch=branch,
        commit=commit,
        tracked_changes=tracked_changes,
        untracked_files=untracked_files,
    )


def _configured_upstream(repository_root: Path) -> str | None:
    """Return the current branch's configured upstream reference."""

    completed = _execute_git(
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
        cwd=repository_root,
    )

    if completed.returncode != 0:
        return None

    upstream = completed.stdout.strip()
    return upstream or None


def _configured_remote(
    repository_root: Path,
    branch: str,
) -> str | None:
    """Return the remote configured for the current branch."""

    if branch == "(detached HEAD)":
        return None

    completed = _execute_git(
        "config",
        "--get",
        f"branch.{branch}.remote",
        cwd=repository_root,
    )

    if completed.returncode != 0:
        return None

    remote = completed.stdout.strip()
    return remote or None


def collect_remote_state(
    local_state: LocalState,
    *,
    refresh: bool = False,
) -> RemoteState:
    """Collect the local branch's relationship to its upstream."""

    if not refresh:
        return RemoteState(status="not refreshed")

    upstream = _configured_upstream(local_state.repository_root)

    if upstream is None:
        return RemoteState(status="no upstream configured")

    remote = _configured_remote(
        local_state.repository_root,
        local_state.branch,
    )

    if remote is None:
        return RemoteState(
            status="unavailable",
            upstream=upstream,
            detail="The upstream remote could not be identified.",
        )

    try:
        _run_git(
            "fetch",
            "--no-tags",
            remote,
            cwd=local_state.repository_root,
        )

        counts = _run_git(
            "rev-list",
            "--left-right",
            "--count",
            f"HEAD...{upstream}",
            cwd=local_state.repository_root,
        )

        count_parts = counts.split()

        if len(count_parts) != 2:
            raise StateError(
                "Git returned an unexpected ahead/behind result."
            )

        ahead, behind = (int(value) for value in count_parts)
    except (StateError, ValueError) as exc:
        return RemoteState(
            status="unavailable",
            upstream=upstream,
            detail=str(exc),
        )

    if ahead == 0 and behind == 0:
        status = "synchronized"
    elif ahead > 0 and behind == 0:
        status = "locally ahead"
    elif ahead == 0 and behind > 0:
        status = "locally behind"
    else:
        status = "diverged"

    return RemoteState(
        status=status,
        upstream=upstream,
        ahead=ahead,
        behind=behind,
    )


def format_state_report(
    local_state: LocalState,
    remote_state: RemoteState | None = None,
    artifact_inventory: ArtifactInventory | None = None,
    build_state: BuildStateEvidence | None = None,
    known_good: KnownGoodEvidence | None = None,
) -> str:
    """Format collected State evidence for a human reader."""

    observed_remote = remote_state or RemoteState(
        status="not refreshed"
    )

    lines = [
        "ClawForge State",
        f"Repository: {local_state.repository_root}",
        f"Branch: {local_state.branch}",
        f"Commit: {local_state.commit}",
        f"Working tree: {local_state.working_tree}",
        f"Tracked changes: {len(local_state.tracked_changes)}",
        f"Untracked files: {len(local_state.untracked_files)}",
        f"Remote state: {observed_remote.status}",
    ]

    if observed_remote.upstream is not None:
        lines.append(f"Upstream: {observed_remote.upstream}")

    if observed_remote.ahead is not None:
        lines.append(f"Ahead: {observed_remote.ahead}")

    if observed_remote.behind is not None:
        lines.append(f"Behind: {observed_remote.behind}")

    if observed_remote.detail is not None:
        lines.append(f"Remote detail: {observed_remote.detail}")

    if artifact_inventory is not None:
        artifact_status = (
            "complete"
            if artifact_inventory.missing_count == 0
            and not artifact_inventory.issues
            else "incomplete"
        )

        lines.extend(
            [
                f"Artifact inventory: {artifact_status}",
                f"Stable anchors: {len(artifact_inventory.anchors)}",
                f"Build records: {len(artifact_inventory.builds)}",
                (
                    "Foundation principles: "
                    f"{len(artifact_inventory.foundation)}"
                ),
                (
                    "Accepted/Frozen ADRs: "
                    f"{len(artifact_inventory.decisions)}"
                ),
                (
                    "Missing artifacts: "
                    f"{artifact_inventory.missing_count}"
                ),
                (
                    "Discovery issues: "
                    f"{len(artifact_inventory.issues)}"
                ),
            ]
        )

        missing_records = tuple(
            record
            for record in artifact_inventory.records
            if record.status == "missing"
        )

        if missing_records:
            lines.append("Missing artifact details:")
            lines.extend(
                (
                    f"  [{record.category}] "
                    f"{record.relative_path}"
                )
                for record in missing_records
            )

        if artifact_inventory.issues:
            lines.append("Artifact discovery issues:")
            lines.extend(
                f"  {issue}"
                for issue in artifact_inventory.issues
            )

    if build_state is not None:
        build_status = (
            "consistent"
            if build_state.is_consistent
            else "inconsistent"
        )

        lines.extend(
            [
                f"Build state: {build_status}",
                (
                    "Completed builds: "
                    f"{len(build_state.completed_builds)}"
                ),
            ]
        )

        if build_state.current_build is not None:
            lines.append(
                "Current build: "
                f"{build_state.current_build.identifier} - "
                f"{build_state.current_build.title}"
            )
        elif build_state.no_active_build_declared:
            lines.append("Current build: none declared")
        elif build_state.current_builds:
            lines.append(
                "Current build: ambiguous "
                f"({len(build_state.current_builds)} declarations)"
            )
        else:
            lines.append("Current build: unavailable")

        if build_state.current_status is not None:
            lines.append(
                f"Current status: {build_state.current_status}"
            )
        elif build_state.current_statuses:
            lines.append(
                "Current status: ambiguous "
                f"({len(build_state.current_statuses)} declarations)"
            )
        else:
            lines.append("Current status: not declared")

        if build_state.known_good_state is not None:
            lines.append(
                "Known Good State: "
                f"{build_state.known_good_state}"
            )
        elif build_state.known_good_states:
            lines.append(
                "Known Good State: ambiguous "
                f"({len(build_state.known_good_states)} declarations)"
            )
        else:
            lines.append("Known Good State: not declared")

        lines.append(
            f"Build-state issues: {len(build_state.issues)}"
        )

        if build_state.issues:
            lines.append("Build-state issue details:")
            lines.extend(
                f"  {issue}"
                for issue in build_state.issues
            )

    if known_good is not None:
        if known_good.commit_exists is True:
            commit_exists = "yes"
        elif known_good.commit_exists is False:
            commit_exists = "no"
        else:
            commit_exists = "unknown"

        lines.extend(
            [
                (
                    "Known Good verification: "
                    f"{known_good.status}"
                ),
                (
                    "Declared Known Good commit: "
                    f"{known_good.declared_commit or 'not declared'}"
                ),
                (
                    "Known Good commit exists: "
                    f"{commit_exists}"
                ),
            ]
        )

        if known_good.resolved_commit is not None:
            lines.append(
                "Resolved Known Good commit: "
                f"{known_good.resolved_commit}"
            )

        if known_good.detail is not None:
            lines.append(
                f"Known Good detail: {known_good.detail}"
            )

    if local_state.tracked_changes:
        lines.append("Tracked change details:")
        lines.extend(
            f"  {item}" for item in local_state.tracked_changes
        )

    if local_state.untracked_files:
        lines.append("Untracked file details:")
        lines.extend(
            f"  {item}" for item in local_state.untracked_files
        )

    return "\n".join(lines)


def run_state(
    start: Path | None = None,
    *,
    refresh_remote: bool = False,
) -> int:
    """Collect and print repository State evidence."""

    try:
        local_state = collect_local_state(start)
    except StateError as exc:
        print(f"State unavailable: {exc}", file=sys.stderr)
        return 2

    remote_state = collect_remote_state(
        local_state,
        refresh=refresh_remote,
    )

    artifact_inventory = discover_artifacts(
        local_state.repository_root
    )

    build_state = inspect_build_state(
        local_state.repository_root
    )

    known_good = inspect_known_good(
        local_state.repository_root,
        build_state.known_good_state,
    )

    print(
        format_state_report(
            local_state,
            remote_state,
            artifact_inventory,
            build_state,
            known_good,
        )
    )
    return 0