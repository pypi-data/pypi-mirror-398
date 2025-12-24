"""
This module contains the CLI entrypoint for CLIs invoked for a local repo
"""

import click

from opendapi.cli.repos.local.runners.local.main import cli as local_runner_cli


@click.group()
def cli():
    """
    This is the entrypoint for CLI invocations from a local repository.

    Please specify which runner you want to use (for local this is generally 'local'),
    in addition to which OpenDapi command, and any relevant options.
    """
    return


cli.add_command(local_runner_cli, name="local")
