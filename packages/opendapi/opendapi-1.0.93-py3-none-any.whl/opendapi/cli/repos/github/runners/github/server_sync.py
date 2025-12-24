"""
CLI for collecting dapi file information at the base commit andhead commit,
analyzing them, uploading the required information to the DAPI server,
and then starting the server driven CICD.

This command is invoked in a github CI runner for a github repo and a single runtime:
`opendapi github github server-sync`
"""

# pylint: disable=duplicate-code

import click

from opendapi.adapters.dapi_server import CICDIntegration
from opendapi.cli.common import get_opendapi_config_from_root
from opendapi.cli.context_agnostic import (
    cicd_init,
    cicd_persist_files,
    cicd_start,
    collect_collected_files,
    server_sync_minimal_schemas,
)
from opendapi.cli.options import (
    OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION,
    SKIP_DBT_INTEGRATION_BASE_GENERATION_OPTION,
    SKIP_DBT_INTEGRATION_HEAD_GENERATION_OPTION,
    SKIP_RUNTIME_INTEGRATION_BASE_GENERATION_OPTION,
    SKIP_RUNTIME_INTEGRATION_HEAD_GENERATION_OPTION,
    dapi_server_options,
    dev_options,
    generation_options,
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
@generation_options
@opendapi_run_options
# github repo options
@repo_options
# github repo github runner options
@runner_options
def cli(**kwargs):
    """
    CLI for collecting dapi file information at the base commit andhead commit,
    analyzing them, uploading the required information to the DAPI server,
    and then starting the server driven CICD.

    This command is invoked in a buildkite CI runner for a github repo and a single runtime:
        `opendapi github github server-sync`
    """

    runtime_skip_generation_at_base = kwargs[
        SKIP_RUNTIME_INTEGRATION_BASE_GENERATION_OPTION.name
    ]
    runtime_skip_generation_at_head = kwargs[
        SKIP_RUNTIME_INTEGRATION_HEAD_GENERATION_OPTION.name
    ]
    dbt_skip_generation_at_base = kwargs[
        SKIP_DBT_INTEGRATION_BASE_GENERATION_OPTION.name
    ]
    dbt_skip_generation_at_head = kwargs[
        SKIP_DBT_INTEGRATION_HEAD_GENERATION_OPTION.name
    ]

    change_trigger_event = construct_change_trigger_event(kwargs)
    opendapi_config = kwargs.get(
        OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION.name
    ) or get_opendapi_config_from_root(
        local_spec_path=kwargs.get("local_spec_path"),
        validate_config=True,
    )
    runtime = opendapi_config.assert_single_runtime()

    base_collected_files = collect_collected_files(
        opendapi_config,
        change_trigger_event=change_trigger_event,
        commit_type=CommitType.BASE,
        runtime_skip_generation=runtime_skip_generation_at_base,
        dbt_skip_generation=dbt_skip_generation_at_base,
        minimal_schemas=server_sync_minimal_schemas(),
        runtime=runtime,
        commit_already_checked_out=False,
        kwargs=kwargs,
    )
    head_collected_files = collect_collected_files(
        opendapi_config,
        change_trigger_event=change_trigger_event,
        commit_type=CommitType.HEAD,
        runtime_skip_generation=runtime_skip_generation_at_head,
        dbt_skip_generation=dbt_skip_generation_at_head,
        minimal_schemas=server_sync_minimal_schemas(),
        runtime=runtime,
        commit_already_checked_out=True,
        kwargs=kwargs,
    )

    run_id = kwargs["github_run_id"]
    run_attempt = kwargs["github_run_attempt"]
    run_number = kwargs["github_run_number"]
    cicd_location_id, s3_upload_data = cicd_init(
        opendapi_config,
        change_trigger_event,
        kwargs,
        should_write_cicd_initialized_file=False,
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
