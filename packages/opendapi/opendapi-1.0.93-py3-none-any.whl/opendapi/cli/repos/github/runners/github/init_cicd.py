"""
CLI for initializing the server driven CICD writing the CICD ID to a file
for use by other commands for uploading files to the DAPI server
and starting the server driven CICD.

This command is invoked in a github CI runner for a github repo:
`opendapi github github init-cicd`
"""

# pylint: disable=duplicate-code

import click

from opendapi.cli.common import get_opendapi_config_from_root
from opendapi.cli.context_agnostic import cicd_init
from opendapi.cli.options import (
    OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION,
    dapi_server_options,
    dev_options,
    opendapi_run_options,
)
from opendapi.cli.repos.github.options import repo_options
from opendapi.cli.repos.github.runners.github.options import (
    construct_change_trigger_event,
    runner_options,
)


@click.command()
# common options
@dapi_server_options
@dev_options
@opendapi_run_options
# github repo options
@repo_options
# github repo github runner options
@runner_options
def cli(**kwargs):
    """
    CLI for initializing the server driven CICD writing the CICD ID to a file
    for use by other commands for uploading files to the DAPI server
    and starting the server driven CICD.

        This command is invoked in a github CI runner for a github repo:
        `opendapi github github init-cicd`
    """

    opendapi_config = kwargs.get(
        OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION.name
    ) or get_opendapi_config_from_root(
        local_spec_path=kwargs.get("local_spec_path"),
        validate_config=True,
    )
    change_trigger_event = construct_change_trigger_event(kwargs)
    cicd_init(
        opendapi_config,
        change_trigger_event,
        kwargs,
    )
