"""
CLI for starting the server driven CICD after all
necessary files have been uploaded to the DAPI server.

This command is invoked in a github CI runner for a github repo:
`opendapi github github start-cicd`
"""

# pylint: disable=duplicate-code

import click

from opendapi.adapters.dapi_server import CICDIntegration
from opendapi.cli.common import get_opendapi_config_from_root
from opendapi.cli.context_agnostic import cicd_start
from opendapi.cli.options import (
    OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION,
    cicd_param_options,
    dapi_server_options,
    dev_options,
    git_options,
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
@git_options
@opendapi_run_options
@cicd_param_options
# github repo options
@repo_options
# github repo github runner options
@runner_options
def cli(**kwargs):
    """
    CLI for starting the server driven CICD after all
    necessary files have been uploaded to the DAPI server.

        This command is invoked in a github CI runner for a github repo:
        `opendapi github github start-cicd`
    """

    cicd_location_id = kwargs["cicd_location_id"]
    change_trigger_event = construct_change_trigger_event(kwargs)
    opendapi_config = kwargs.get(
        OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION.name
    ) or get_opendapi_config_from_root(
        local_spec_path=kwargs.get("local_spec_path"),
        validate_config=True,
    )

    run_id = kwargs["github_run_id"]
    run_attempt = kwargs["github_run_attempt"]
    run_number = kwargs["github_run_number"]

    cicd_start(
        lambda dr, mf: dr.cicd_start_github_github(
            cicd_location_id=cicd_location_id,
            run_id=run_id,
            run_attempt=run_attempt,
            run_number=run_number,
            metadata_file=mf,
        ),
        cicd_location_id,
        opendapi_config,
        change_trigger_event,
        CICDIntegration.GITHUB_GITHUB,
        {
            "run_id": run_id,
            "run_attempt": run_attempt,
            "run_number": run_number,
        },
        kwargs,
    )
