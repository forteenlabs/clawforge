from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnownGoodEvidence:
    """Git evidence associated with a declared Known Good State."""

    declared_commit: str | None
    resolved_commit: str | None
    status: str
    detail: str | None = None

    @property
    def commit_exists(self) -> bool | None:
        """Return whether the declared commit was found."""

        if self.status in {"current", "ancestor", "not ancestor"}:
            return True

        if self.status == "missing":
            return False

        return None


def _execute_git(
    repository_root: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    """Run one read-only Git command."""

    return subprocess.run(
        ["git", *arguments],
        cwd=repository_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _diagnostic(
    completed: subprocess.CompletedProcess[str],
) -> str:
    """Return the best available Git diagnostic."""

    return (
        completed.stderr.strip()
        or completed.stdout.strip()
        or "Git returned no diagnostic information."
    )


def inspect_known_good(
    repository_root: Path,
    declared_commit: str | None,
) -> KnownGoodEvidence:
    """Verify a declared Known Good State without creating one."""

    if declared_commit is None:
        return KnownGoodEvidence(
            declared_commit=None,
            resolved_commit=None,
            status="not declared",
        )

    root = repository_root.resolve()
    commit_expression = f"{declared_commit}^{{commit}}"

    try:
        resolved = _execute_git(
            root,
            "rev-parse",
            "--verify",
            "--quiet",
            commit_expression,
        )
    except FileNotFoundError:
        return KnownGoodEvidence(
            declared_commit=declared_commit,
            resolved_commit=None,
            status="unavailable",
            detail="Git is not available on PATH.",
        )

    if resolved.returncode == 1:
        return KnownGoodEvidence(
            declared_commit=declared_commit,
            resolved_commit=None,
            status="missing",
            detail=(
                "The declared Known Good State could not be "
                "resolved as a commit."
            ),
        )

    if resolved.returncode != 0:
        return KnownGoodEvidence(
            declared_commit=declared_commit,
            resolved_commit=None,
            status="unavailable",
            detail=_diagnostic(resolved),
        )

    resolved_commit = resolved.stdout.strip()

    head = _execute_git(
        root,
        "rev-parse",
        "--verify",
        "HEAD^{commit}",
    )

    if head.returncode != 0:
        return KnownGoodEvidence(
            declared_commit=declared_commit,
            resolved_commit=resolved_commit,
            status="unavailable",
            detail=_diagnostic(head),
        )

    head_commit = head.stdout.strip()

    if resolved_commit == head_commit:
        return KnownGoodEvidence(
            declared_commit=declared_commit,
            resolved_commit=resolved_commit,
            status="current",
        )

    relationship = _execute_git(
        root,
        "merge-base",
        "--is-ancestor",
        resolved_commit,
        "HEAD",
    )

    if relationship.returncode == 0:
        status = "ancestor"
        detail = None
    elif relationship.returncode == 1:
        status = "not ancestor"
        detail = None
    else:
        status = "unavailable"
        detail = _diagnostic(relationship)

    return KnownGoodEvidence(
        declared_commit=declared_commit,
        resolved_commit=resolved_commit,
        status=status,
        detail=detail,
    )
