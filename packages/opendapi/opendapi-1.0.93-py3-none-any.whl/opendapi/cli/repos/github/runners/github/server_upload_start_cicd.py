"""
CLI for loading the base and headcollected dapi file information,
analyzing them, uploading the required information to the DAPI server,
and then starting the server driven CICD.

This command is invoked in a github CI runner for a github repo and a single runtime:
`opendapi github github server-upload-start-cicd`
"""

# pylint: disable=duplicate-code

import click

from opendapi.adapters.dapi_server import CICDIntegration
from opendapi.cli.common import get_opendapi_config_from_root
from opendapi.cli.context_agnostic import (
    cicd_init,
    cicd_persist_files,
    cicd_start,
    load_locally_persisted_collected_files,
)
from opendapi.cli.options import (
    OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION,
    dapi_server_options,
    dev_options,
    git_options,
    opendapi_run_options,
    schema_integration_options,
)
from opendapi.cli.repos.github.options import repo_options
from opendapi.cli.repos.github.runners.github.options import (
    construct_change_trigger_event,
    runner_options,
)
from opendapi.defs import CommitType


@click.command()
# common options
@dapi_server_options
@schema_integration_options
@dev_options
@git_options
@opendapi_run_options
# github repo options
@repo_options
# github repo github runner options
@runner_options
def cli(**kwargs):
    """
    CLI for loading the base and headcollected dapi file information,
    analyzing them, uploading the required information to the DAPI server,
    and then starting the server driven CICD.

        This command is invoked in a github CI runner for a github repo and a single runtime:
        `opendapi github github server-upload-start-cicd`
    """

    change_trigger_event = construct_change_trigger_event(kwargs)
    opendapi_config = kwargs.get(
        OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION.name
    ) or get_opendapi_config_from_root(
        local_spec_path=kwargs.get("local_spec_path"),
        validate_config=True,
    )
    runtime = opendapi_config.assert_single_runtime()

    head_collected_files = load_locally_persisted_collected_files(
        opendapi_config,
        CommitType.HEAD,
        runtime,
    )
    base_collected_files = load_locally_persisted_collected_files(
        opendapi_config,
        CommitType.BASE,
        runtime,
    )

    run_id = kwargs["github_run_id"]
    run_attempt = kwargs["github_run_attempt"]
    run_number = kwargs["github_run_number"]
    cicd_location_id, s3_upload_data = cicd_init(
        opendapi_config,
        change_trigger_event,
        kwargs,
    )
    cicd_persist_files(
        base_collected_files,
        head_collected_files,
        change_trigger_event,
        opendapi_config,
        s3_upload_data,
        runtime,
        kwargs,
    )
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
