"""
This module contains the CLI entrypoint for CLIs invoked for a local repo
given a local runner - i.e. `opendapi local local *`
"""

import click

from opendapi.cli.context_agnostic import repo_runner_cli
from opendapi.cli.options import dapi_server_options, git_options, opendapi_run_options
from opendapi.cli.repos.local.runners.local.base_collect import cli as base_collect_cli
from opendapi.cli.repos.local.runners.local.generate import cli as generate_cli
from opendapi.cli.repos.local.runners.local.head_collect import cli as head_collect_cli
from opendapi.cli.repos.local.runners.local.head_collect_write_locally import (
    cli as head_collect_write_locally_cli,
)
from opendapi.cli.repos.local.runners.local.options import (
    construct_change_trigger_event,
)
from opendapi.cli.repos.local.runners.local.write_locally import (
    cli as write_locally_cli,
)


@click.group()
# common options
@dapi_server_options
@git_options
@opendapi_run_options
def cli(**kwargs):
    """
    This is the entrypoint for CLI invocations from a local repository
    given a local runner.

    Please specify which OpenDapi command, and any relevant options.
    """
    change_trigger_event = construct_change_trigger_event(kwargs)
    sentry_tags = {
        "cmd": click.get_current_context().invoked_subcommand,
        "repository_type": "local",
        "runner": "local",
    }
    repo_runner_cli(change_trigger_event, sentry_tags, kwargs)


cli.add_command(generate_cli, name="generate")
cli.add_command(base_collect_cli, name="base-collect")
cli.add_command(head_collect_cli, name="head-collect")
cli.add_command(head_collect_write_locally_cli, name="head-collect-write-locally")
cli.add_command(write_locally_cli, name="write-locally")
