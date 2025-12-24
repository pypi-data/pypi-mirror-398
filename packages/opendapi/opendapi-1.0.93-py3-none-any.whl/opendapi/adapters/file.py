"""File adapter."""

import importlib
import inspect
import os
from typing import Generator, List, Optional

from opendapi.adapters.git import iter_git_files
from opendapi.logging import logger

DEFAULT_EXCLUDE_DIRS = [
    "__pycache__",
    ".git",
    "node_modules",
    ".venv",
    "virtualenv",
    ".virtualenv",
    "venv",
    "env",
    "dist",
    "build",
    "target",
    "out",
    ".mypy_cache",
    ".pytest_cache",
    "tmp",
    "temp",
    "cache",
    "dbt_packages",
    "packages",
    "Test",
    "test",
    "Tests",
    "tests",
    "e2e",
]


def iter_files(
    root_dir: str,  # abs path
    *,
    suffixes: Optional[List[str]] = None,
    rel_prefixes: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
) -> Generator[str, None, None]:
    """Iterate through files in a root directory"""

    # exact dir-name match is faster/safer than regex here
    exclude_set = list(set(exclude_dirs or []))
    if not os.path.isabs(root_dir):
        raise ValueError("root_dir must be an absolute path")
    if rel_prefixes and any(os.path.isabs(p) for p in rel_prefixes):
        raise ValueError("rel_prefixes must be relative paths")

    # Build absolute, trailing-sep allowed prefixes for pruning
    if rel_prefixes:
        abs_prefixes = []
        for p in rel_prefixes:
            ap = p if os.path.isabs(p) else os.path.join(root_dir, p)
            ap = os.path.abspath(ap)
            if not ap.endswith(os.sep):
                ap += os.sep
            abs_prefixes.append(ap)
    else:
        abs_prefixes = None

    suffix_tuple = tuple(suffixes)

    for current_root, dirs, filenames in os.walk(root_dir, topdown=True):
        # Prune early if no allowed prefix lies under this root
        if abs_prefixes:
            # Ensure root has a trailing sep for proper startswith checks
            current_root_with_sep = (
                current_root if current_root.endswith(os.sep) else current_root + os.sep
            )
            # Note this check only conserves traversal but does not filter out files already traversed
            if not any(
                p.startswith(current_root_with_sep)
                or current_root_with_sep.startswith(p)
                for p in abs_prefixes
            ):
                dirs[:] = []  # don't descend further
                continue

        # Prune excluded directories by *name* (not path)
        dirs[:] = [d for d in dirs if d not in exclude_set]

        # Collect matching files
        for filename in filenames:
            full_filepath = os.path.join(current_root, filename)
            # Check for suffix match
            if full_filepath.endswith(suffix_tuple):
                # Check for prefix match
                if abs_prefixes and not any(
                    full_filepath.startswith(p) for p in abs_prefixes
                ):
                    continue
                yield full_filepath


def find_files_with_suffix(
    root_dir: str,
    suffixes: List[str],
    rel_prefixes: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
    use_git: bool = True,
):
    """Find files with a suffix in a root directory"""
    # Normalize inputs
    root_dir = os.path.abspath(root_dir)
    all_exclude_dirs = (
        exclude_dirs + DEFAULT_EXCLUDE_DIRS if exclude_dirs else DEFAULT_EXCLUDE_DIRS
    )
    is_git_present = os.path.exists(os.path.join(root_dir, ".git"))
    if use_git and is_git_present:
        try:
            return list(
                iter_git_files(
                    root_dir,
                    suffixes=suffixes,
                    rel_prefixes=rel_prefixes,
                    exclude_dirs=all_exclude_dirs,
                    include_untracked=True,
                    return_absolute=True,
                )
            )
        except Exception as exc:  # pylint: disable=broad-except
            # shouldn't happen as we usually operate on git repos, but just in case
            logger.exception(
                "Could not use git to find files in %s with %s", root_dir, str(exc)
            )

    return list(
        iter_files(
            root_dir,
            suffixes=suffixes,
            rel_prefixes=rel_prefixes,
            exclude_dirs=all_exclude_dirs,
        )
    )


def find_subclasses_in_directory(
    root_dir: str,
    base_class,
    rel_prefixes: List[str] = None,
    exclude_dirs: List[str] = None,
):
    """Find subclasses of a base class in modules in a root_dir"""
    subclasses = []
    filenames = find_files_with_suffix(
        root_dir,
        [".py"],
        exclude_dirs=exclude_dirs,
        rel_prefixes=rel_prefixes,
    )
    for py_file in filenames:
        rel_py_file = os.path.relpath(py_file, root_dir)
        module_name = os.path.splitext(rel_py_file)[0].replace(os.sep, ".")
        try:
            module = importlib.import_module(module_name)
            for _, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, base_class)
                    and obj != base_class
                    and obj not in subclasses
                ):
                    subclasses.append(obj)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Could not import module %s with %s", module_name, str(exc))
    return subclasses


def text_file_loader(fullpath: str) -> str:
    """Load a text file"""
    with open(fullpath, encoding="utf-8") as f:
        return f.read()
