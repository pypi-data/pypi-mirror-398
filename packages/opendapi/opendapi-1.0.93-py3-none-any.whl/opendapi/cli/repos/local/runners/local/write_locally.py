"""
CLI for loading the persisted information
at current state and base commit and then writing the appropriate
final dapis to the local directory, when invoked locally:
`opendapi local local write-locally`
"""

# pylint: disable=duplicate-code

import click

from opendapi.cli.common import get_opendapi_config_from_root
from opendapi.cli.context_agnostic import (
    load_locally_persisted_collected_files,
    reconcile_collected_files_across_runtimes,
    write_locally,
)
from opendapi.cli.options import OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION, dev_options
from opendapi.defs import CommitType


@click.command()
@dev_options
def cli(**kwargs):
    """
    CLI for loading the persisted information
    at current state and base commit and then writing the appropriate
    final dapis to the local directory:
    `opendapi local local write-locally`
    """
    opendapi_config = kwargs.get(
        OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION.name
    ) or get_opendapi_config_from_root(
        local_spec_path=kwargs.get("local_spec_path"),
        validate_config=True,
    )

    base_collected_files_by_runtime = {}
    head_collected_files_by_runtime = {}
    for runtime in opendapi_config.runtime_names:
        base_collected_files_by_runtime[runtime] = (
            load_locally_persisted_collected_files(
                opendapi_config,
                CommitType.BASE,
                runtime,
            )
        )
        head_collected_files_by_runtime[runtime] = (
            load_locally_persisted_collected_files(
                opendapi_config,
                CommitType.CURRENT,
                runtime,
            )
        )

    base_collected_files = reconcile_collected_files_across_runtimes(
        opendapi_config,
        base_collected_files_by_runtime,
    )
    head_collected_files = reconcile_collected_files_across_runtimes(
        opendapi_config,
        head_collected_files_by_runtime,
    )

    write_locally(
        opendapi_config,
        head_collected_files,
        base_collected_files,
        kwargs,
    )
