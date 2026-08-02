from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


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

    print(format_state_report(local_state, remote_state))
    return 0