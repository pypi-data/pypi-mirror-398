# pylint: disable=too-many-instance-attributes, too-many-branches, too-many-boolean-expressions
"""Git adapter for OpenDAPI"""

from __future__ import annotations

import os
import re
import subprocess  # nosec: B404
from dataclasses import asdict, dataclass
from typing import Generator, List, Optional, Tuple, Union

from opendapi.defs import REFS_PREFIXES, CommitType
from opendapi.logging import logger


def run_git(
    cwd: str,
    args: list[str],
    *,
    decode_to_str: bool = False,
) -> Union[str, bytes]:
    """
    Non-streaming git runner - returns values directly.

    Args:
        cwd: Working directory for the git command
        args: Git command arguments (without 'git')
        decode_to_str: If True, decode output to string and strip whitespace

    Returns:
        Command output as bytes or decoded string
    """
    cmd = ["git", "--no-pager", *args]

    try:
        out = subprocess.run(  # nosec: B603
            cmd,
            cwd=cwd,
            capture_output=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.decode("utf-8", "replace") if exc.stderr else str(exc)
        logger.exception("git %s failed: %s", args, err)
        raise RuntimeError(f"git {args} failed: {err}") from exc

    return out if not decode_to_str else out.decode("utf-8", "replace").strip()


def stream_git(
    cwd: str,
    args: list[str],
    *,
    delimiter: Optional[bytes] = None,  # b"\x00" for -z, b"\n" for lines
    decode_to_str: bool = False,  # if False, don't decode
) -> Generator[Union[str, bytes], None, None]:
    """
    Streaming git runner - yields values as they become available.

    Args:
        cwd: Working directory for the git command
        args: Git command arguments (without 'git')
        delimiter: Split output by this delimiter (None for raw chunks)
        decode_to_str: If True, decode output to string

    Yields:
        Command output chunks as bytes or decoded strings
    """
    cmd = ["git", "--no-pager", *args]

    try:
        with subprocess.Popen(  # nosec: B603
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as proc:
            if delimiter is None:
                # raw chunk streaming
                for chunk in iter(lambda: proc.stdout.read(65536), b""):
                    yield (
                        chunk if not decode_to_str else chunk.decode("utf-8", "replace")
                    )
            else:
                buf = b""
                for chunk in iter(lambda: proc.stdout.read(65536), b""):
                    buf += chunk
                    *parts, buf = buf.split(delimiter)
                    for p in parts:
                        yield p if not decode_to_str else p.decode("utf-8", "replace")
                if buf:
                    yield buf if not decode_to_str else buf.decode("utf-8", "replace")

            rc = proc.wait()
            if rc != 0:
                err = proc.stderr.read().decode("utf-8", "replace")
                logger.exception("git %s exited %s: %s", args, rc, err.strip())
                raise RuntimeError(f"git {args} exited {rc}: {err.strip()}")
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.decode("utf-8", "replace") if exc.stderr else str(exc)
        logger.exception("git %s failed: %s", args, err)
        raise RuntimeError(f"git {args} failed: {err}") from exc


def iter_git_files(
    repo_root: str,  # abs path
    *,
    suffixes: Optional[List[str]] = None,
    rel_prefixes: Optional[List[str]] = None,  # repo-rel
    exclude_dirs: Optional[List[str]] = None,  # dir names (no globs)
    include_untracked: bool = False,
    return_absolute: bool = False,
) -> Generator[str, None, None]:
    """
    Yield absolute file paths from `git ls-files`, filtered by:
      - rel_prefixes: limit to these subtrees
      - exclude_dirs: exclude any files under these directory names
      - suffixes: restrict to these file suffixes (e.g., [".sql", ".ini"])
      - include_untracked: include untracked-but-unignored files
    Uses stream_git() with NUL-delimited output for robustness & streaming.
    """
    # Normalize prefixes to repo-relative POSIX
    prefixes = rel_prefixes or ["."]
    if not os.path.isabs(repo_root):
        raise ValueError("repo_root must be an absolute path")

    if any(os.path.isabs(p) for p in prefixes):
        raise ValueError("rel_prefixes must be relative paths")

    # Build include pathspecs (prefix × suffix)
    if suffixes:
        pathspecs = []
        for sfx in suffixes:
            for pref in prefixes:
                if pref != ".":
                    pathspecs += [f"{pref}/**/*{sfx}", f"{pref}/*{sfx}"]
                else:
                    pathspecs += [f"**/*{sfx}", f"*{sfx}"]
    else:
        pathspecs = prefixes

    # Build exclude pathspecs (dir-name based)
    excl_names = list(set(exclude_dirs or []))
    exclude_specs = [f":(exclude,glob)**/{d}/**" for d in excl_names]

    args = ["ls-files", "-z"]
    untracked_args = ["--others", "--exclude-standard"]
    specs = pathspecs + exclude_specs

    seen = set()
    # Stream NUL-delimited records, decoded to str
    for rel_path in stream_git(
        repo_root, [*args, "--", *specs], delimiter=b"\x00", decode_to_str=True
    ):
        if not rel_path or rel_path in seen:  # defensive (trailing NUL)
            continue
        seen.add(rel_path)
        yield os.path.join(repo_root, rel_path) if return_absolute else rel_path

    if include_untracked:
        for rel_path in stream_git(
            repo_root,
            [*args, *untracked_args, "--", *specs],
            delimiter=b"\x00",
            decode_to_str=True,
        ):
            if not rel_path or rel_path in seen:  # defensive (trailing NUL)
                continue
            seen.add(rel_path)
            yield os.path.join(repo_root, rel_path) if return_absolute else rel_path


def get_commit_timestamp_str(cwd: str, commit_sha: str) -> str:
    """Get the commit timestamp string."""
    return run_git(
        cwd,
        [
            "show",
            "--format=%cd",
            "--no-patch",
            "--date=iso-strict",
            commit_sha,
        ],
        decode_to_str=True,
    )


def get_merge_base(cwd: str, current_ref: str, base_ref: str) -> str:
    """Get the merge base of two refs."""
    merge_base = run_git(cwd, ["merge-base", current_ref, base_ref], decode_to_str=True)
    logger.info("Merge base of %s and %s is %s", current_ref, base_ref, merge_base)
    return merge_base


def get_upstream_commit_sha(cwd: str, ref: str, steps: int) -> str:
    """Get the upstream commit SHA."""
    if steps < 0:
        raise ValueError("Steps must be non-negative")

    upstream_sha = run_git(
        cwd,
        ["rev-parse", f"{ref}~{steps}"],
        decode_to_str=True,
    )
    logger.info("Upstream commit SHA of %s~%s is %s", ref, steps, upstream_sha)
    return upstream_sha


def get_checked_out_branch_or_commit(cwd: str) -> str:
    """Get the checked out branch or commit."""
    # if a branch is checked out, returns the branch name, if a commit is, it returns HEAD
    branch_name_or_head = run_git(
        cwd, ["rev-parse", "--abbrev-ref", "HEAD"], decode_to_str=True
    )
    # if the branch is detached, it returns the commit hash
    if branch_name_or_head == "HEAD":
        return run_git(cwd, ["rev-parse", "HEAD"], decode_to_str=True)
    return branch_name_or_head


def _get_current_stash_names_with_index(cwd: str) -> List[Tuple[int, str]]:
    return [
        (i, stash.split(": ")[-1])
        for i, stash in enumerate(
            run_git(cwd, ["stash", "list"], decode_to_str=True).split("\n")
        )
    ]


def add_named_stash(cwd: str, stash_name: str) -> bool:
    """
    Add a named stash. Note that index not returned
    since it changes with other stashes.

    Returns True if a stash was created, False otherwise.
    """
    # if there is nothing to stash this does not raise or fail, but instead
    # just does not create the named stash
    current_stashes = [stash for _, stash in _get_current_stash_names_with_index(cwd)]
    if stash_name in current_stashes:
        raise ValueError(f"Stash {stash_name} already exists")
    result = run_git(
        cwd, ["stash", "save", "--include-untracked", stash_name], decode_to_str=True
    )
    return result != "No local changes to save"


def pop_named_stash(cwd: str, stash_name: str) -> None:
    """Pop a named stash."""
    current_stashes_w_index = _get_current_stash_names_with_index(cwd)
    stash_index = next(
        (i for i, stash in current_stashes_w_index if stash == stash_name),
        None,
    )
    if stash_index is None:
        raise ValueError(f"Stash {stash_name} not found")
    run_git(cwd, ["stash", "pop", f"stash@{{{stash_index}}}"])


def get_uncommitted_changes(cwd: str) -> str:
    """Get the uncommitted changes."""
    return run_git(cwd, ["diff", "--name-only"], decode_to_str=True)


def get_untracked_changes(cwd: str) -> str:
    """Get the untracked changes."""
    return run_git(
        cwd, ["ls-files", "--others", "--exclude-standard"], decode_to_str=True
    )


def check_if_uncommitted_or_untracked_changes_exist(
    cwd: str, log_exception: bool = True
) -> bool:
    """Check if uncommitted or untracked changes exist."""
    uncommitted_changes = get_uncommitted_changes(cwd)
    untracked_changes = get_untracked_changes(cwd)
    if (uncommitted_changes or untracked_changes) and log_exception:
        logger.exception(
            "Uncommitted: %s, Untracked: %s", uncommitted_changes, untracked_changes
        )

    return bool(uncommitted_changes or untracked_changes)


class GitCommitStasher:
    """
    Context manager to stash changes while checking out a commit.
    """

    def __init__(self, cwd: str, stash_name: str, commit_sha: str):
        # args
        self.cwd = cwd
        self.stash_name = stash_name
        self.commit_sha = commit_sha
        # internal state
        self.currently_stashed = False
        self.stash_created = False
        self.pre_checkout_sha = None
        # reduce noise about detached head
        run_git(self.cwd, ["config", "--global", "advice.detachedHead", "false"])

    def _reset(self):
        """
        Reset the state of the stasher.
        """
        run_git(self.cwd, ["checkout", self.pre_checkout_sha])

        if self.stash_created:
            pop_named_stash(self.cwd, self.stash_name)

        self.currently_stashed = False
        self.stash_created = False
        self.pre_checkout_sha = None

    def __enter__(self) -> GitCommitStasher:
        if self.currently_stashed:
            raise ValueError("Already stashed")
        self.stash_created = add_named_stash(self.cwd, self.stash_name)
        # sanity check
        if check_if_uncommitted_or_untracked_changes_exist(self.cwd):
            self._reset()
            raise RuntimeError("You have uncommitted or untracked changes after stash")
        self.currently_stashed = True
        self.pre_checkout_sha = get_checked_out_branch_or_commit(self.cwd)
        run_git(self.cwd, ["checkout", self.commit_sha])
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if not self.currently_stashed:
            raise ValueError("Not stashed")

        try:
            if check_if_uncommitted_or_untracked_changes_exist(self.cwd):
                raise RuntimeError("File changes were detected while stashed.")

        finally:
            self._reset()


@dataclass(frozen=True)
class ChangeTriggerEvent:
    """
    Summary information for git changes
    """

    where: str
    before_change_sha: str = None
    event_type: Optional[str] = None
    after_change_sha: Optional[str] = None
    after_change_sha_timestamp: Optional[str] = None
    repo_api_url: Optional[str] = None
    repo_html_url: Optional[str] = None
    repo_owner: Optional[str] = None
    git_ref: Optional[str] = None
    pull_request_number: Optional[int] = None
    auth_token: Optional[str] = None
    workspace: Optional[str] = None
    head_sha: Optional[str] = None
    repository: Optional[str] = None
    repo_full_name: Optional[str] = None
    pull_request_link: Optional[str] = None
    original_pr_author: Optional[str] = None
    workflow_name: Optional[str] = None

    def __post_init__(self):
        """Post init checks"""
        if self.where not in ["local", "github"] or self.before_change_sha is None:
            raise ValueError(
                "Where should be either local or github."
                " Before change SHA is required"
            )

        if self.is_github_event:
            if (
                self.event_type is None
                or self.after_change_sha is None
                or self.repo_api_url is None
                or self.repo_html_url is None
                or self.repo_owner is None
            ):
                raise ValueError(
                    "Event type, after change SHA, repo API URL, repo HTML URL, "
                    "repo owner are required"
                )

            if self.is_pull_request_event:
                if self.pull_request_number is None:
                    raise ValueError("Pull request number is required")
                if self.pull_request_link is None:
                    raise ValueError("Pull request link is required")

        if self.is_push_event:
            if self.git_ref is None:
                raise ValueError("Git ref is required")

    @property
    def is_local_event(self) -> bool:
        """Check if the event is a local event"""
        return self.where == "local"

    @property
    def is_github_event(self) -> bool:
        """Check if the event is a github event"""
        return self.where == "github"

    @property
    def is_pull_request_event(self) -> bool:
        """Check if the event is a pull request event"""
        return self.event_type == "pull_request"

    @property
    def is_push_event(self) -> bool:
        """Check if the event is a push event"""
        return self.event_type == "push"

    @property
    def integration_type(self) -> str:
        """Get the integration type"""
        return "direct" if self.where == "local" else self.where

    @property
    def branch(self) -> Optional[str]:
        """Get the branch"""
        if not self.git_ref:
            return None  # pragma: no cover

        return next(
            (
                re.split(prefix, self.git_ref)[-1]
                for prefix in REFS_PREFIXES
                if re.match(prefix, self.git_ref)
            ),
            self.git_ref,
        )

    @property
    def as_dict(self) -> dict:
        """Get the event as a dictionary"""
        return asdict(self)

    def commit_type_to_sha(
        self, commit_type: CommitType, enforce: bool = True
    ) -> Optional[str]:
        """Get the SHA for the commit type"""
        commit_sha = (
            self.before_change_sha
            if commit_type is CommitType.BASE
            else self.after_change_sha
        )
        if commit_sha is None and enforce:  # pragma: no cover
            raise ValueError("Commit SHA is required")
        return commit_sha
