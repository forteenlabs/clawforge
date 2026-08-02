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


def _run_git(*arguments: str, cwd: Path) -> str:
    """Run a read-only Git command and return its standard output."""

    try:
        completed = subprocess.run(
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


def format_state_report(state: LocalState) -> str:
    """Format collected State evidence for a human reader."""

    lines = [
        "ClawForge State",
        f"Repository: {state.repository_root}",
        f"Branch: {state.branch}",
        f"Commit: {state.commit}",
        f"Working tree: {state.working_tree}",
        f"Tracked changes: {len(state.tracked_changes)}",
        f"Untracked files: {len(state.untracked_files)}",
        "Remote state: not refreshed",
    ]

    if state.tracked_changes:
        lines.append("Tracked change details:")
        lines.extend(f"  {item}" for item in state.tracked_changes)

    if state.untracked_files:
        lines.append("Untracked file details:")
        lines.extend(f"  {item}" for item in state.untracked_files)

    return "\n".join(lines)


def run_state(start: Path | None = None) -> int:
    """Collect and print local State evidence."""

    try:
        state = collect_local_state(start)
    except StateError as exc:
        print(f"State unavailable: {exc}", file=sys.stderr)
        return 2

    print(format_state_report(state))
    return 0