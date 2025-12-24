"""
CLI for collecting dapi file information at the base commit andhead commit,
analyzing them, uploading the required information to the DAPI server,
and then starting the server driven CICD.

This command is invoked in a buildkite CI runner for a github repo and a single runtime:
`opendapi github buildkite server-sync`
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
from opendapi.cli.repos.github.runners.buildkite.options import (
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
# github repo bk runner options
@runner_options
def cli(**kwargs):  # pylint: disable=too-many-locals
    """
    CLI for collecting dapi file information at the base commit andhead commit,
    analyzing them, uploading the required information to the DAPI server,
    and then starting the server driven CICD.

    This command is invoked in a buildkite CI runner for a github repo and a single runtime:
    `opendapi github buildkite server-sync`
    """

    runtime_skip_generation_at_base = kwargs.get(
        SKIP_RUNTIME_INTEGRATION_BASE_GENERATION_OPTION.name, False
    )

    runtime_skip_generation_at_head = kwargs.get(
        SKIP_RUNTIME_INTEGRATION_HEAD_GENERATION_OPTION.name, False
    )

    dbt_skip_generation_at_base = kwargs.get(
        SKIP_DBT_INTEGRATION_BASE_GENERATION_OPTION.name, True
    )

    dbt_skip_generation_at_head = kwargs.get(
        SKIP_DBT_INTEGRATION_HEAD_GENERATION_OPTION.name, True
    )

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

    # NOTE: we may want to make this an envvar set by the script,
    #       but this works for now. The ideal case is we pull this from BK API,
    #       which we will need anyway for DBT, but this is fine for now.
    build_id = kwargs["buildkite_build_id"]
    build_number = kwargs["buildkite_build_number"]
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
        lambda dr, mf: dr.cicd_start_github_buildkite(
            cicd_location_id=cicd_location_id,
            build_id=build_id,
            build_number=build_number,
            metadata_file=mf,
        ),
        cicd_location_id,
        opendapi_config,
        change_trigger_event,
        CICDIntegration.GITHUB_BUILDKITE,
        {
            "build_id": build_id,
            "build_number": build_number,
        },
        kwargs,
    )
