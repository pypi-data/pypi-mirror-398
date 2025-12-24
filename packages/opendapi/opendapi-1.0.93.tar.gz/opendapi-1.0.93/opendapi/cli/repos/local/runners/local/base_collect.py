"""
CLI for collecting dapi file information at the base commit and then persisting
it for later use when invoked locally: `opendapi local local base-collect`
"""

# pylint: disable=duplicate-code

import click

from opendapi.cli.common import get_opendapi_config_from_root
from opendapi.cli.context_agnostic import (
    collect_collected_files,
    get_maximal_schemas,
    locally_persist_collected_files,
)
from opendapi.cli.options import (
    BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION,
    CURRENTLY_CHECKED_OUT_COMMIT_SHA_PARAM_NAME_WITH_OPTION,
    OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION,
    SKIP_DBT_INTEGRATION_BASE_GENERATION_OPTION,
    SKIP_RUNTIME_INTEGRATION_BASE_GENERATION_OPTION,
    dev_options,
    generation_options,
    git_options,
    opendapi_run_options,
    runtime_options,
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
@runtime_options
@opendapi_run_options
def cli(**kwargs):
    """
    CLI for collecting dapi file information at the base commit and then persisting
    it for later use: `opendapi local local base-collect`
    """
    runtime_skip_generation_at_base = kwargs[
        SKIP_RUNTIME_INTEGRATION_BASE_GENERATION_OPTION.name
    ]

    dbt_skip_generation_at_base = kwargs[
        SKIP_DBT_INTEGRATION_BASE_GENERATION_OPTION.name
    ]

    runtime = kwargs["runtime"]
    opendapi_config = kwargs.get(
        OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION.name
    ) or get_opendapi_config_from_root(
        local_spec_path=kwargs.get("local_spec_path"),
        validate_config=True,
    )
    opendapi_config.assert_runtime_exists(runtime)
    base_commit_sha = kwargs.get(BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION.name)
    if not base_commit_sha:  # pragma: no cover
        raise click.ClickException(
            f"Base commit SHA is required for base collect, please provide it using the option: "
            f"{BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION.name}"
        )
    # for base collect we default to False if not set (None)
    currently_checked_out_commit_sha = kwargs.get(
        CURRENTLY_CHECKED_OUT_COMMIT_SHA_PARAM_NAME_WITH_OPTION.name
    )
    if (
        currently_checked_out_commit_sha
        and currently_checked_out_commit_sha != base_commit_sha
    ):
        raise click.ClickException(
            "The currently checked out commit SHA does not match the before change SHA"
        )

    collected_files = collect_collected_files(
        opendapi_config,
        change_trigger_event=construct_change_trigger_event(kwargs),
        commit_type=CommitType.BASE,
        runtime_skip_generation=runtime_skip_generation_at_base,
        dbt_skip_generation=dbt_skip_generation_at_base,
        minimal_schemas=get_maximal_schemas(),
        runtime=runtime,
        commit_already_checked_out=currently_checked_out_commit_sha == base_commit_sha,
        kwargs=kwargs,
    )
    locally_persist_collected_files(
        collected_files,
        opendapi_config,
        commit_type=CommitType.BASE,
        runtime=runtime,
    )
