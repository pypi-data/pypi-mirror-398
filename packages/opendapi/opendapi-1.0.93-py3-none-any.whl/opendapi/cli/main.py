"""Entrypoint for the OpenDAPI CLI."""

import click
import sentry_sdk

from opendapi.cli.init import cli as init_cli
from opendapi.cli.repos.github.main import cli as github_repo_cli
from opendapi.cli.repos.local.main import cli as local_repo_cli


@click.group()
def cli():
    """
    Welcome to OpenDapi!

    This CLI is used to generate, enrich, and register Dapi files - your
    one stop shop for tracking data APIs.

    Depending on if you are running this locally, or for a Github repo on
    a Github hosted runner, etc., different options are required, so please peruse
    via --help to see what options are relevant to you.
    """
    return


def cli_wrapper():
    """A wrapper for all commands so we can capture exceptions and log them"""
    try:
        cli()
    except Exception as exp:  # pylint: disable=broad-except
        # This catches all the exceptions that are uncaught by click.
        # For eg: If an application developer raises click.Abort(), click handles
        # it and exits the program. This is expected behavior and we will not send
        # these to sentry. However, if the application fails due to an internal
        # error, we will catch it and log it.
        sentry_sdk.capture_exception(exp)
        sentry_sdk.flush()
        raise exp


# Add commands to the CLI
cli.add_command(init_cli, name="init")
cli.add_command(github_repo_cli, name="github")
cli.add_command(local_repo_cli, name="local")
