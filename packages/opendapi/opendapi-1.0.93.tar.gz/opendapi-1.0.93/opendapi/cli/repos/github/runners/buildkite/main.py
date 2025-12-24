"""
This module contains the CLI entrypoint for CLIs invoked for a Github remote repo
given a Buildkite hosted runner - i.e. `opendapi github github *`
"""

# pylint: disable=duplicate-code

import click

from opendapi.cli.context_agnostic import repo_runner_cli
from opendapi.cli.options import (
    SKIP_DBT_INTEGRATION_HEAD_GENERATION_OPTION,
    dapi_server_options,
    generation_options,
    git_options,
    opendapi_run_options,
    schema_integration_options,
)
from opendapi.cli.repos.github.options import repo_options
from opendapi.cli.repos.github.runners.buildkite.base_collect import (
    cli as base_collect_cli,
)
from opendapi.cli.repos.github.runners.buildkite.head_collect import (
    cli as head_collect_cli,
)
from opendapi.cli.repos.github.runners.buildkite.head_collect_server_upload import (
    cli as head_collect_server_upload_cli,
)
from opendapi.cli.repos.github.runners.buildkite.head_collect_server_upload_start_cicd import (
    cli as head_collect_server_upload_start_cicd_cli,
)
from opendapi.cli.repos.github.runners.buildkite.init_cicd import cli as init_cicd_cli
from opendapi.cli.repos.github.runners.buildkite.options import (
    construct_change_trigger_event,
    runner_options,
)
from opendapi.cli.repos.github.runners.buildkite.run import cli as run_cli
from opendapi.cli.repos.github.runners.buildkite.server_sync import (
    cli as server_sync_cli,
)
from opendapi.cli.repos.github.runners.buildkite.server_upload import (
    cli as server_upload_cli,
)
from opendapi.cli.repos.github.runners.buildkite.server_upload_start_cicd import (
    cli as server_upload_start_cicd_cli,
)
from opendapi.cli.repos.github.runners.buildkite.start_cicd import cli as start_cicd_cli


def _should_skip_dbt_cloud__push(kwargs):
    """
    Check if the `generate` command should be skipped

    Skip scenarios:
    1. If integrated with dbt Cloud
        a. Skip if push event - since DBT cloud doesnt run on pushes to main by default
    """
    should_wait_on_dbt_cloud = kwargs["dbt_cloud_url"] is not None
    # NOTE see if there is another way to get this
    is_push_event = not bool(kwargs["buildkite_pull_request"])

    return should_wait_on_dbt_cloud and is_push_event


@click.group()
# common options
@dapi_server_options
@schema_integration_options
@generation_options
@git_options
@opendapi_run_options
# github repo options
@repo_options
# github repo bk runner options
@runner_options
def cli(**kwargs):
    """
    This is the entrypoint for CLI invocations from a Github remote repo
    given a Buildkite hosted runner.

    Please specify which OpenDapi command, and any relevant options.
    """

    # make accessible
    SKIP_DBT_INTEGRATION_HEAD_GENERATION_OPTION.set_as_envvar_if_none(
        kwargs, _should_skip_dbt_cloud__push(kwargs)
    )

    change_trigger_event = construct_change_trigger_event(kwargs)
    sentry_tags = {
        "cmd": click.get_current_context().invoked_subcommand,
        "repository_type": "github",
        "runner": "buildkite",
        # the build is not rerun, but a new job is created each time,
        # so this is what would be common
        "common_rerun_id": kwargs["buildkite_build_id"],
        "workspace": change_trigger_event.workspace,
        "event_name": change_trigger_event.event_type,
        "repo": change_trigger_event.repository,
        "bk_build_id": kwargs["buildkite_build_id"],
        "bk_build_number": kwargs["buildkite_build_number"],
    }
    repo_runner_cli(change_trigger_event, sentry_tags, kwargs)


cli.add_command(run_cli, name="run")
cli.add_command(server_sync_cli, name="server-sync")
cli.add_command(server_upload_cli, name="server-upload")
cli.add_command(server_upload_start_cicd_cli, name="server-upload-start-cicd")
cli.add_command(base_collect_cli, name="base-collect")
cli.add_command(head_collect_cli, name="head-collect")
cli.add_command(head_collect_server_upload_cli, name="head-collect-server-upload")
cli.add_command(init_cicd_cli, name="init-cicd")
cli.add_command(
    head_collect_server_upload_start_cicd_cli,
    name="head-collect-server-upload-start-cicd",
)
cli.add_command(start_cicd_cli, name="start-cicd")
