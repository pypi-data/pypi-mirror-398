"""
CLI for loading the base and head collected dapi file information,
analyzing them, uploading the required information to the DAPI server

This command is invoked in a buildkite CI runner for a github repo and a single runtime:
`opendapi github buildkite server-upload`
"""

# pylint: disable=duplicate-code

import click

from opendapi.cli.common import get_opendapi_config_from_root
from opendapi.cli.context_agnostic import (
    cicd_get_s3_upload_data,
    cicd_persist_files,
    load_locally_persisted_collected_files,
)
from opendapi.cli.options import (
    OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION,
    cicd_param_options,
    dapi_server_options,
    dev_options,
    git_options,
    opendapi_run_options,
    runtime_options,
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
@git_options
@opendapi_run_options
@runtime_options
@cicd_param_options
# github repo options
@repo_options
# github repo bk runner options
@runner_options
def cli(**kwargs):
    """
    CLI for loading the base and head collected dapi file information,
    analyzing them, uploading the required information to the DAPI server

    This command is invoked in a buildkite CI runner for a github repo and a single runtime:
    `opendapi github buildkite server-upload`
    """

    cicd_location_id = kwargs["cicd_location_id"]
    runtime = kwargs["runtime"]
    change_trigger_event = construct_change_trigger_event(kwargs)
    opendapi_config = kwargs.get(
        OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION.name
    ) or get_opendapi_config_from_root(
        local_spec_path=kwargs.get("local_spec_path"),
        validate_config=True,
    )
    opendapi_config.assert_runtime_exists(runtime)

    base_collected_files = load_locally_persisted_collected_files(
        opendapi_config,
        CommitType.BASE,
        runtime,
    )
    head_collected_files = load_locally_persisted_collected_files(
        opendapi_config,
        CommitType.HEAD,
        runtime,
    )

    s3_upload_data = cicd_get_s3_upload_data(
        cicd_location_id,
        change_trigger_event,
        opendapi_config,
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
