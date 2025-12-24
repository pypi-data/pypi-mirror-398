"""
CLI for collecting dapi file information at the base commit andhead commit,
analyzing them, uploading the required information to the DAPI server,
and then starting the server driven CICD.

This command is invoked in a buildkite CI runner for a github repo and a single runtime:
`opendapi github buildkite run`
"""

import click

from opendapi.cli.context_agnostic import repo_runner_run_cli
from opendapi.cli.options import (
    dapi_server_options,
    dev_options,
    generation_options,
    git_options,
    opendapi_run_options,
    schema_integration_options,
)
from opendapi.cli.repos.github.options import repo_options
from opendapi.cli.repos.github.runners.buildkite.options import runner_options
from opendapi.cli.repos.github.runners.buildkite.server_sync import (
    cli as server_sync_cli,
)


@click.command()
# common options
@dapi_server_options
@schema_integration_options
@dev_options
@generation_options
@git_options
@opendapi_run_options
# github repo options
@repo_options
# github repo bk runner options
@runner_options
def cli(**kwargs):
    """
    CLI for collecting dapi file information at the base commit andhead commit,
    analyzing them, uploading the required information to the DAPI server,
    and then starting the server driven CICD.

    This command is invoked in a buildkite CI runner for a github repo and a single runtime:
    `opendapi github buildkite run`
    """

    # Run register last to ensure the DAPI files are registered and unregistered
    # Register will also validate the DAPI files in the backend

    commands = {
        "server-sync": server_sync_cli,
    }

    repo_runner_run_cli(commands, kwargs)
