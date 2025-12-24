"""
Houses options for invocation for a Github remote repository
that are common to all runners (i.e. Github hosted runner. Buildkite)
"""

import click


def repo_options(func: click.core.Command) -> click.core.Command:
    """
    Set of click options required for all invocations for a
    Github remote repository.
    """
    options = []
    for option in reversed(options):
        func = option(func)  # pragma: no cover
    return func
