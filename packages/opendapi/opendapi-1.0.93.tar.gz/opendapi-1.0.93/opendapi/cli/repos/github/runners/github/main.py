"""
This module contains the CLI entrypoint for CLIs invoked for a Github remote repo
given a Github hosted runner - i.e. `opendapi github github *`
"""

import click

from opendapi.cli.common import print_cli_output
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
from opendapi.cli.repos.github.runners.github.base_collect import (
    cli as base_collect_cli,
)
from opendapi.cli.repos.github.runners.github.head_collect import (
    cli as head_collect_cli,
)
from opendapi.cli.repos.github.runners.github.head_collect_server_upload import (
    cli as head_collect_server_upload_cli,
)
from opendapi.cli.repos.github.runners.github.head_collect_server_upload_start_cicd import (
    cli as head_collect_server_upload_start_cicd_cli,
)
from opendapi.cli.repos.github.runners.github.init_cicd import cli as init_cicd_cli
from opendapi.cli.repos.github.runners.github.options import (
    construct_change_trigger_event,
    runner_options,
)
from opendapi.cli.repos.github.runners.github.run import cli as run_cli
from opendapi.cli.repos.github.runners.github.server_sync import cli as server_sync_cli
from opendapi.cli.repos.github.runners.github.server_upload import (
    cli as server_upload_cli,
)
from opendapi.cli.repos.github.runners.github.server_upload_start_cicd import (
    cli as server_upload_start_cicd_cli,
)
from opendapi.cli.repos.github.runners.github.start_cicd import cli as start_cicd_cli
from opendapi.cli.repos.github.runners.github.utils import is_ignored_author


def _should_skip_dbt_cloud__push(kwargs):
    """
    Check if the `generate` command should be skipped

    Skip scenarios:
    1. If integrated with dbt Cloud
        a. Skip if push event - since DBT cloud doesnt run on pushes to main by default
    """
    should_wait_on_dbt_cloud = kwargs["dbt_cloud_url"] is not None
    is_push_event = kwargs["github_event_name"] == "push"

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
# github repo github runner options
@runner_options
def cli(**kwargs):
    """
    This is the entrypoint for CLI invocations from a Github remote repo
    given a Github hosted runner.

    Please specify which OpenDapi command, and any relevant options.
    """

    change_trigger_event = construct_change_trigger_event(kwargs)
    if is_ignored_author(change_trigger_event.original_pr_author):
        print_cli_output(
            "Skipping run because pull request is by an ignored author - like dependabot - "
            "for which Github Actions do not allow access to secrets, so the run cannot proceed."
            " Since this is a scenario in which no model changes should be made, "
            "the run is skipped, as to no block committing to the repo."
        )
        click.get_current_context().exit(0)

    # make accessible
    SKIP_DBT_INTEGRATION_HEAD_GENERATION_OPTION.set_as_envvar_if_none(
        kwargs, _should_skip_dbt_cloud__push(kwargs)
    )

    sentry_tags = {
        "cmd": click.get_current_context().invoked_subcommand,
        "repository_type": "github",
        "runner": "github",
        "run_attempt": kwargs["github_run_attempt"],
        "common_rerun_id": kwargs["github_run_id"],
        "workspace": change_trigger_event.workspace,
        "event_name": change_trigger_event.event_type,
        "repo": change_trigger_event.repository,
        "gh_run_attempt": kwargs["github_run_attempt"],
        "gh_run_id": kwargs["github_run_id"],
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
