"""
This module contains the CLI entrypoint for CLIs invoked for a Github remote repo
"""

import click

from opendapi.cli.repos.github.runners.buildkite.main import cli as buildkite_runner_cli
from opendapi.cli.repos.github.runners.github.main import cli as github_runner_cli


@click.group()
def cli():
    """
    This is the entrypoint for CLI invocations from a Github remote repository.

    Please specify which runner you want to use (i.e. `github`
    if you are running on a Github hosted runner),
    in addition to which OpenDapi command, and any relevant options.
    """
    return


cli.add_command(buildkite_runner_cli, name="buildkite")
cli.add_command(github_runner_cli, name="github")
