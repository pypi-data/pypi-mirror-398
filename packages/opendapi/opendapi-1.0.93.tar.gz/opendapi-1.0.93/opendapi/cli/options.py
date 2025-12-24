"""Shared options used by OpenDAPI CLI."""

import functools
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, TypeVar

import click

from opendapi.adapters.dapi_server import DAPIServerConfig
from opendapi.cli.common import load_opendapi_config
from opendapi.config import OpenDAPIConfig

S = TypeVar("S")
T = TypeVar("T")


def construct_dapi_server_config(
    kwargs: dict, opendapi_config: OpenDAPIConfig
) -> DAPIServerConfig:
    """Construct the DAPI server configuration from the CLI arguments."""
    return DAPIServerConfig(
        server_host=kwargs["dapi_server_host"],
        api_key=kwargs["dapi_server_api_key"],
        mainline_branch_name=kwargs["mainline_branch_name"],
        register_on_merge_to_mainline=kwargs["register_on_merge_to_mainline"],
        woven_integration_mode=opendapi_config.integration_mode,
        woven_configuration=kwargs["woven_configuration"],
    )


@dataclass
class ParamNameWithOption:
    """Dataclass to hold the name and option for a parameter."""

    option: Callable[[Callable], click.Option]
    convert_to_argument: Callable[[S], T] = lambda x: x

    @functools.cached_property
    def __click_params(self):
        """Get thewrapped click params"""
        return self.option(lambda: True).__click_params__[0]

    @property
    def name(self) -> str:
        """Get the name of the parameter from the option."""
        return self.__click_params.name

    @property
    def envvar(self) -> str:
        """Get the environment variable name of the parameter from the option."""
        return self.__click_params.envvar

    @property
    def callback(self) -> Optional[Callable[[click.Context, click.Option, T], S]]:
        """Return the callback of the option if applicable"""
        return self.__click_params.callback  # pragma: no cover

    def set_as_envvar_if_none(self, kwargs: dict, value: S):
        """Set the value as an environment variable if it does not exist in kwargs."""
        if kwargs.get(self.name) is None:
            os.environ[self.envvar] = self.convert_to_argument(value)


def dev_options(func: click.core.Command) -> click.core.Command:
    """Set of click options required for most commands."""
    options = [
        click.option(
            "--local-spec-path",
            default=None,
            envvar="LOCAL_SPEC_PATH",
            help="Use specs in the local path instead of the DAPI server",
            show_envvar=False,
        ),
        click.option(
            "--always-write-generated-dapis",
            is_flag=True,
            default=False,
            envvar="ALWAYS_WRITE_GENERATED_DAPIS",
            help="Write the generated dapis even if they have not changed",
            show_envvar=False,
        ),
    ]
    for option in reversed(options):
        func = option(func)
    return func


def dapi_server_options(func: click.core.Command) -> click.core.Command:
    """Set of click options required for the dapi server commands."""
    options = [
        click.option(
            "--dapi-server-host",
            envvar="DAPI_SERVER_HOST",
            show_envvar=True,
            default="https://api.woven.dev",
            help="The host of the DAPI server",
        ),
        click.option(
            "--dapi-server-api-key",
            envvar="DAPI_SERVER_API_KEY",
            show_envvar=True,
            help="The API key for the DAPI server",
        ),
    ]
    for option in reversed(options):
        func = option(func)
    return func


BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION = ParamNameWithOption(
    option=click.option(
        "--base-commit-sha",
        envvar="BASE_COMMIT_SHA",
        show_envvar=True,
        default=None,
        help="The SHA of the base commit",
    )
)

HEAD_COMMIT_SHA_PARAM_NAME_WITH_OPTION = ParamNameWithOption(
    option=click.option(
        "--head-commit-sha",
        envvar="HEAD_COMMIT_SHA",
        show_envvar=True,
        default=None,
        help="The SHA of the head commit",
    )
)


def _validate_isoformat(ctx, param, value):  # pylint: disable=unused-argument
    try:
        _ = datetime.fromisoformat(value) if value is not None else value
        return value
    except ValueError:
        raise click.BadParameter(f"Invalid ISO format: {value}") from None


HEAD_COMMIT_SHA_TIMESTAMP_PARAM_NAME_WITH_OPTION = ParamNameWithOption(
    option=click.option(
        "--head-commit-sha-timestamp",
        envvar="HEAD_COMMIT_SHA_TIMESTAMP",
        show_envvar=True,
        default=None,
        help="The timestamp of the head commit",
        callback=_validate_isoformat,
    ),
)

CURRENTLY_CHECKED_OUT_COMMIT_SHA_PARAM_NAME_WITH_OPTION = ParamNameWithOption(
    option=click.option(
        "--currently-checked-out-commit-sha",
        envvar="CURRENTLY_CHECKED_OUT_COMMIT_SHA",
        show_envvar=True,
        default=None,
        help="The SHA of the currently checked out commit",
    )
)


def git_options(func: click.core.Command) -> click.core.Command:
    """Set of click options required for the git commands."""
    for option in (
        BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION.option,
        HEAD_COMMIT_SHA_PARAM_NAME_WITH_OPTION.option,
        HEAD_COMMIT_SHA_TIMESTAMP_PARAM_NAME_WITH_OPTION.option,
        CURRENTLY_CHECKED_OUT_COMMIT_SHA_PARAM_NAME_WITH_OPTION.option,
    ):
        func = option(func)
    return func


def _load_opendapi_config(  # pylint: disable=unused-argument
    ctx, param, value
) -> Optional[OpenDAPIConfig]:
    return value and load_opendapi_config(value, validate_config=True)


OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION = ParamNameWithOption(
    option=click.option(
        "--opendapi-config",
        envvar="OPENDAPI_CONFIG",
        show_envvar=True,
        default=None,
        help="The serialized OpenDAPI config",
        callback=_load_opendapi_config,
    )
)


def opendapi_run_options(func: click.core.Command) -> click.core.Command:
    """Set of click options required for the client commands for debugging."""
    options = [
        click.option(
            "--mainline-branch-name",
            default="main",
            envvar="MAINLINE_BRANCH_NAME",
            show_envvar=True,
            help="The name of the mainline branch to compare against",
        ),
        click.option(
            "--s3-persist-threadpool-size",
            default=8,
            envvar="S3_PERSIST_THREADPOOL_SIZE",
            help="Threadpool size for persisting DAPI files to S3",
            show_envvar=False,
        ),
        click.option(
            "--register-on-merge-to-mainline",
            is_flag=True,
            default=True,
            envvar="REGISTER_ON_MERGE_TO_MAINLINE",
            help="Register DAPI files on merge to mainline branch",
            show_envvar=False,
        ),
        click.option(
            "--woven-configuration",
            type=click.Choice(["done", "in_progress"], case_sensitive=True),
            default="done",
            envvar="WOVEN_CONFIGURATION",
            help="Is Woven's configuration done or in progress",
            show_envvar=False,
        ),
        click.option(
            "--skip-client-config",
            is_flag=True,
            default=False,
            envvar="SKIP_CLIENT_CONFIG",
            help="Skip fetching client config from the server",
            show_envvar=False,
        ),
        OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION.option,
    ]
    for option in reversed(options):
        func = option(func)
    return func


def cicd_param_options(func: click.core.Command) -> click.core.Command:
    """Set of click options required for the CICD parameters."""
    options = [
        click.option(
            "--cicd-location-id",
            envvar="CICD_LOCATION_ID",
            show_envvar=True,
            help="The CICD Location ID",
            type=str,
            required=True,
        ),
    ]
    for option in reversed(options):
        func = option(func)
    return func


def schema_integration_options(func: click.core.Command) -> click.core.Command:
    """
    Set of click options required for the Schema integrations.
    KBTODO: Need to pass this through to the validator instead of pulling from os.environ
    """
    options = [
        click.option(
            "--dbt-cloud-url",
            envvar="DAPI_DBT_CLOUD_URL",
            show_envvar=True,
            help="The host of the dbt Cloud integration",
            default=None,
            type=str,
        ),
        click.option(
            "--dbt-cloud-api-key",
            envvar="DAPI_DBT_CLOUD_API_KEY",
            show_envvar=True,
            help="The API key for the dbt cloud integration",
        ),
        click.option(
            "--dbt-cloud-retry-count",
            envvar="DAPI_DBT_CLOUD_RETRY_COUNT",
            show_envvar=True,
            help="The retry count for dbt cloud integration",
        ),
        click.option(
            "--dbt-cloud-retry-interval",
            envvar="DAPI_DBT_CLOUD_RETRY_INTERVAL",
            show_envvar=True,
            help="The retry interval for dbt cloud integration",
        ),
        click.option(
            "--dapi-dbt-fast-fail",
            envvar="DAPI_DBT_FAST_FAIL",
            show_envvar=True,
            default=False,
            help="Fast fail if the opendapi dbt cloud job fails",
        ),
        click.option(
            "--liquibase-updatesql-gradle-command",
            envvar="LIQUIBASE_UPDATESQL_GRADLE_COMMAND",
            show_envvar=True,
            help="The Gradle command to run updateSQL for Liquibase",
        ),
    ]
    for option in reversed(options):
        func = option(func)
    return func


SKIP_RUNTIME_INTEGRATION_BASE_GENERATION_OPTION = ParamNameWithOption(
    option=click.option(
        "--skip-runtime-integration-base-generation",
        is_flag=True,
        envvar="SKIP_RUNTIME_INTEGRATION_BASE_GENERATION",
        help="Skip the generation step for runtime integrations at the base commit",
        show_envvar=False,
    ),
)

SKIP_RUNTIME_INTEGRATION_HEAD_GENERATION_OPTION = ParamNameWithOption(
    option=click.option(
        "--skip-runtime-integration-head-generation",
        is_flag=True,
        envvar="SKIP_RUNTIME_INTEGRATION_HEAD_GENERATION",
        help="Skip the generation step for runtime integrations at the head commit",
        show_envvar=False,
    ),
)

SKIP_DBT_INTEGRATION_BASE_GENERATION_OPTION = ParamNameWithOption(
    option=click.option(
        "--skip-dbt-integration-base-generation",
        is_flag=True,
        default=True,
        envvar="SKIP_DBT_INTEGRATION_BASE_GENERATION",
        help="Skip the generation step for dbt integrations at the base commit",
        show_envvar=False,
    ),
)

SKIP_DBT_INTEGRATION_HEAD_GENERATION_OPTION = ParamNameWithOption(
    option=click.option(
        "--skip-dbt-integration-head-generation",
        type=bool,
        # Since click is meant to decorate a (usually) explicitly-typed function,
        # all options must have a value - either from the user or default - to be able
        # to invoke the decorated function.
        # Therefore, if this default was False we would not be able to differentiate
        # between a user passing in False, or it being False due to the default,
        # and we need to know this since if it was not passed in we may use fallback logic
        # (i.e. in the DBT push case). We therefore make the default None.
        default=None,
        envvar="SKIP_DBT_INTEGRATION_HEAD_GENERATION",
        help="Skip the generation step for dbt integrations at the head commit",
        show_envvar=False,
        required=False,
    ),
    convert_to_argument=lambda x: str(x).lower(),
)


def generation_options(func: click.core.Command) -> click.core.Command:
    """Set of click options required for the generation commands."""
    options = [
        SKIP_RUNTIME_INTEGRATION_BASE_GENERATION_OPTION.option,
        SKIP_RUNTIME_INTEGRATION_HEAD_GENERATION_OPTION.option,
        SKIP_DBT_INTEGRATION_BASE_GENERATION_OPTION.option,
        SKIP_DBT_INTEGRATION_HEAD_GENERATION_OPTION.option,
    ]
    for option in reversed(options):
        func = option(func)
    return func


def runtime_options(func: click.core.Command) -> click.core.Command:
    """Set of click options required for commands that deal with multiple runtimes"""
    options = [
        click.option(
            "--runtime",
            type=str,
            envvar="RUNTIME",
            help="The runtime to use for generation",
            show_envvar=False,
            required=True,
        ),
    ]
    for option in reversed(options):
        func = option(func)
    return func
