"""
CLI for writing dapi files to the local directory,
when invoked locally: `opendapi local local generate`
"""

# pylint: disable=duplicate-code

import click

from opendapi.cli.common import get_opendapi_config_from_root
from opendapi.cli.context_agnostic import (
    collect_collected_files,
    get_maximal_schemas,
    write_locally,
)
from opendapi.cli.options import (
    BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION,
    CURRENTLY_CHECKED_OUT_COMMIT_SHA_PARAM_NAME_WITH_OPTION,
    OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION,
    SKIP_DBT_INTEGRATION_BASE_GENERATION_OPTION,
    SKIP_DBT_INTEGRATION_HEAD_GENERATION_OPTION,
    SKIP_RUNTIME_INTEGRATION_BASE_GENERATION_OPTION,
    SKIP_RUNTIME_INTEGRATION_HEAD_GENERATION_OPTION,
    dev_options,
    generation_options,
    git_options,
    opendapi_run_options,
    schema_integration_options,
)
from opendapi.cli.repos.local.runners.local.options import (
    construct_change_trigger_event,
)
from opendapi.defs import CommitType


@click.command()
@schema_integration_options
@dev_options
@generation_options
@git_options
@opendapi_run_options
def cli(**kwargs):
    """
     CLI for writing dapi files to the local directory:
    `opendapi local local generate`
    """

    if kwargs.get(CURRENTLY_CHECKED_OUT_COMMIT_SHA_PARAM_NAME_WITH_OPTION.name):
        raise click.ClickException(
            "The currently checked out commit SHA is not supported for generate"
        )

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

    opendapi_config = kwargs.get(
        OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION.name
    ) or get_opendapi_config_from_root(
        local_spec_path=kwargs.get("local_spec_path"),
        validate_config=True,
    )
    runtime = opendapi_config.assert_single_runtime()

    base_commit_sha = kwargs.get(BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION.name)
    if not base_commit_sha:  # pragma: no cover
        raise click.ClickException(
            f"Base commit SHA is required for base collect, please provide it using the option: "
            f"{BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION.name}"
        )

    change_trigger_event = construct_change_trigger_event(kwargs)

    base_collected_files = collect_collected_files(
        opendapi_config,
        change_trigger_event=change_trigger_event,
        commit_type=CommitType.BASE,
        runtime_skip_generation=runtime_skip_generation_at_base,
        dbt_skip_generation=dbt_skip_generation_at_base,
        minimal_schemas=get_maximal_schemas(),
        runtime=runtime,
        commit_already_checked_out=False,
        kwargs=kwargs,
    )
    head_collected_files = collect_collected_files(
        opendapi_config,
        change_trigger_event=change_trigger_event,
        commit_type=CommitType.CURRENT,
        runtime_skip_generation=runtime_skip_generation_at_head,
        dbt_skip_generation=dbt_skip_generation_at_head,
        minimal_schemas=get_maximal_schemas(),
        runtime=runtime,
        commit_already_checked_out=True,
        kwargs=kwargs,
    )

    write_locally(
        opendapi_config,
        head_collected_files,
        base_collected_files,
        kwargs,
    )
