"""
Houses options for invocation of a Github remote repo
on a Buildkite hosted runner, in addition for the change_trigger_event construction
"""

from __future__ import annotations

from typing import NamedTuple, Optional

import click

from opendapi.adapters.git import (
    ChangeTriggerEvent,
    get_commit_timestamp_str,
    get_merge_base,
    get_upstream_commit_sha,
)
from opendapi.cli.common import get_root_dir_validated
from opendapi.cli.options import (
    BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION,
    HEAD_COMMIT_SHA_PARAM_NAME_WITH_OPTION,
    HEAD_COMMIT_SHA_TIMESTAMP_PARAM_NAME_WITH_OPTION,
)


class BuildkiteRepoInfo(NamedTuple):
    """
    The repo info for the buildkite repo
    """

    repo_full_name: str
    repo_owner: str
    repo_api_url: str
    repo_html_url: str

    @classmethod
    def from_buildkite_repo(cls, repo_git_notation: str) -> BuildkiteRepoInfo:
        """
        Get the repo info from the buildkite repo
        """
        if repo_git_notation.endswith(".git"):
            repo_git_notation = repo_git_notation[:-4]
        splits = repo_git_notation.split("/")
        repo_owner = splits[-2].split("git@github.com:")[-1]
        repo_name = splits[-1]
        return cls(
            repo_full_name=f"{repo_owner}/{repo_name}",
            repo_owner=repo_owner,
            repo_api_url=f"https://api.github.com/repos/{repo_owner}/{repo_name}",
            repo_html_url=f"https://github.com/{repo_owner}/{repo_name}",
        )


def construct_change_trigger_event(  # pylint: disable=too-many-locals
    kwargs: dict,
) -> ChangeTriggerEvent:
    """
    Construct the ChangeTriggerEvent given that this a Github remote repo
    on a Buildkite hosted runner
    """

    # NOTE see if there is another way of doing this from BK envvars for things like
    # manual triggers etc. (e.g. use BUILDKITE_PIPELINE_DEFAULT_BRANCH != BUILDKITE_BRANCH)
    event_type = "pull_request" if kwargs["buildkite_pull_request"] else "push"
    repo_git_notation = kwargs["buildkite_repo"]
    repo_full_name, repo_owner, repo_api_url, repo_html_url = (
        BuildkiteRepoInfo.from_buildkite_repo(repo_git_notation)
    )

    # can't really see a reason not to use the one from the event, but since
    # we do the same for the timestamp might as well be consistent
    after_change_sha = (
        kwargs.get(HEAD_COMMIT_SHA_PARAM_NAME_WITH_OPTION.name)
        or kwargs["buildkite_commit"]
    )

    if passed_in_base_commit_sha := kwargs.get(
        BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION.name
    ):
        before_change_sha = passed_in_base_commit_sha
    elif event_type == "push":
        before_change_sha = get_upstream_commit_sha(
            get_root_dir_validated(), after_change_sha, 1
        )
    else:
        base_branch = kwargs["buildkite_pull_request_base_branch"]
        # We will use the origin/branch because the runner may not have the local tracking branch
        origin_base_branch = (
            base_branch
            if base_branch.lower().startswith("origin/")
            else f"origin/{base_branch}"
        )
        before_change_sha = get_merge_base(
            get_root_dir_validated(), after_change_sha, origin_base_branch
        )

    git_ref = f"refs/heads/{kwargs['buildkite_branch']}"
    pull_request_number = (
        kwargs["buildkite_pull_request"] if event_type == "pull_request" else None
    )

    head_sha = kwargs["buildkite_commit"]

    pull_request_link = (
        f"{repo_html_url}/pull/{pull_request_number}"
        if event_type == "pull_request"
        else None
    )

    after_change_sha_timestamp = kwargs.get(
        HEAD_COMMIT_SHA_TIMESTAMP_PARAM_NAME_WITH_OPTION.name
    ) or get_commit_timestamp_str(get_root_dir_validated(), after_change_sha)

    return ChangeTriggerEvent(
        where="github",
        event_type=event_type,
        repo_api_url=repo_api_url,
        repo_html_url=repo_html_url,
        repo_owner=repo_owner,
        before_change_sha=before_change_sha,
        after_change_sha=after_change_sha,
        after_change_sha_timestamp=after_change_sha_timestamp,
        git_ref=git_ref,
        pull_request_number=pull_request_number,
        workspace=kwargs["buildkite_build_checkout_path"],
        # NOTE ask why this exists - also check GH one
        head_sha=head_sha,
        # NOTE ask why both
        repository=repo_full_name,
        repo_full_name=repo_full_name,
        pull_request_link=pull_request_link,
        workflow_name=kwargs.get("buildkite_pipeline_name"),
    )


def _convert_to_int_set_to_none_if_false(
    ctx: click.Context,  # pylint: disable=unused-argument
    param: click.Option,  # pylint: disable=unused-argument
    value: str,
) -> Optional[int]:
    return int(value) if value != "false" else None


def _set_to_none_if_empty_string(
    ctx: click.Context,  # pylint: disable=unused-argument
    param: click.Option,  # pylint: disable=unused-argument
    value: str,
) -> Optional[str]:
    return value or None


def runner_options(func: click.core.Command) -> click.core.Command:
    """
    Common options for a Buildkite hosted runner
    """
    options = [
        click.option(
            "--buildkite-pull-request",
            envvar="BUILDKITE_PULL_REQUEST",
            show_envvar=True,
            default="false",
            callback=_convert_to_int_set_to_none_if_false,
            required=True,
        ),
        # NOTE may need to export in hooks
        click.option("--buildkite-repo", envvar="BUILDKITE_REPO"),
        click.option("--buildkite-commit", envvar="BUILDKITE_COMMIT"),
        click.option(
            "--buildkite-pull-request-base-branch",
            envvar="BUILDKITE_PULL_REQUEST_BASE_BRANCH",
            show_envvar=True,
            default="",
            callback=_set_to_none_if_empty_string,
        ),
        click.option("--buildkite-branch", envvar="BUILDKITE_BRANCH"),
        # NOTE may need to export in hooks
        click.option(
            "--buildkite-build-checkout-path", envvar="BUILDKITE_BUILD_CHECKOUT_PATH"
        ),
        click.option("--buildkite-build-id", envvar="BUILDKITE_BUILD_ID"),
        click.option(
            "--buildkite-build-number", envvar="BUILDKITE_BUILD_NUMBER", type=int
        ),
        click.option("--buildkite-pipeline-name", envvar="BUILDKITE_PIPELINE_NAME"),
    ]
    for option in reversed(options):
        func = option(func)
    return func
