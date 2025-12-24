"""
Houses common functionality for running OpenDapi
functions - independent of repo/runner.
"""

# pylint: disable=too-many-lines

from collections import defaultdict
from importlib.metadata import version
from typing import Callable, Dict, Tuple

import click

from opendapi.adapters.dapi_server import CICDIntegration, DAPIRequests
from opendapi.adapters.git import ChangeTriggerEvent
from opendapi.cli.common import (
    OpenDAPIConfig,
    Schemas,
    get_opendapi_config_from_root,
    pretty_print_errors,
    print_cli_output,
)
from opendapi.cli.options import (
    BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION,
    OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION,
    construct_dapi_server_config,
)
from opendapi.cli.utils import (
    cleanup_opendapi_cache,
    cleanup_tmp_state,
    collected_files_tmp_dump,
    collected_files_tmp_load,
    missing_dapi_file_exists,
    write_cicd_initialized_file,
    write_missing_dapis_to_cache,
)
from opendapi.defs import (
    DAPI_CLIENT_REQUIRED_MINIMAL_SCHEMA,
    CommitType,
    OpenDAPIEntity,
)
from opendapi.feature_flags import FeatureFlag, set_feature_flags
from opendapi.logging import LogDistKey, Timer, logger, sentry_init
from opendapi.validators.defs import CollectedFile
from opendapi.validators.validate import collect_and_validate_cached
from opendapi.writers.utils import get_writer_for_entity

########## main ##########


def repo_runner_cli(
    change_trigger_event: ChangeTriggerEvent,
    sentry_tags: dict,
    kwargs: dict,
):
    """
    To be used by the 'main' cli for a repo/runner combo, i.e.
    opendapi.cli.repos.github.runners.buildkite.main.cli

    Takes care of getting common information from DapiServer, setting up sentry,
    etc.
    """
    # first lets make sure that the opendapi config is available
    opendapi_config = kwargs.get(
        OPENDAPI_CONFIG_PARAM_NAME_WITH_OPTION.name
    ) or get_opendapi_config_from_root(
        local_spec_path=kwargs.get("local_spec_path"),
        validate_config=True,
    )

    dapi_server_config = construct_dapi_server_config(kwargs, opendapi_config)
    dapi_requests = None

    BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION.set_as_envvar_if_none(
        kwargs, change_trigger_event.before_change_sha
    )
    if not kwargs.get("skip_client_config"):
        try:
            # Initialize sentry and fetch Feature flags
            # This fails silently if the client config is not available
            # This is temporary to monitor if this actually breaks
            dapi_requests = DAPIRequests(
                dapi_server_config=dapi_server_config,
                trigger_event=change_trigger_event,
            )

            client_config = dapi_requests.get_client_config_from_server()
            sentry_tags.update(client_config.get("sentry_tags", {}))
            sentry_init(
                client_config.get("sentry", {}),
                tags=sentry_tags,
            )
            if client_config.get("fetch_feature_flags", False):
                feature_flags: dict = (
                    dapi_requests.get_client_feature_flags_from_server(
                        [f.value for f in FeatureFlag]
                    )
                )
                set_feature_flags(
                    {
                        FeatureFlag(f): val
                        for f, val in feature_flags.items()
                        if FeatureFlag.has_value(f)
                    }
                )

        except Exception as exp:  # pylint: disable=broad-except
            logger.error("Error fetching client config: %s", exp)


########## run ##########


def repo_runner_run_cli(
    commands: Dict[str, click.Command],
    kwargs: dict,
):
    """
    To be used by the 'run' cli for a repo/runner combo, i.e.
    opendapi.cli.repos.github.runners.buildkite.run.cli

    Given a set of commands, runs then as long as they are not intended to be skipped
    (i.e. a third party integration may not be ready to have generate run yet)
    """
    for command_name, command in commands.items():

        print_cli_output(
            f"Invoking `{command_name}`...",
            color="green",
            bold=True,
        )
        command_params = command.params
        # run's params should always be a superset of all the children's params,
        # and therefore we do unsafe dict access as to not swallow any discrepancies
        command_kwargs = {key.name: kwargs[key.name] for key in command_params}
        with click.Context(command) as ctx:
            ctx.invoke(command, **command_kwargs)


########## CICD general ##########


def server_sync_minimal_schemas() -> Schemas:
    """
    Returns the minimal schemas for server-driven CICD
    """
    # NOTE: Currently only DAPI schemas need minimal schemas
    #       all other schemas produced by the validators are already minimal
    return Schemas.create(
        dapi=DAPI_CLIENT_REQUIRED_MINIMAL_SCHEMA,
    )


def get_maximal_schemas() -> Schemas:
    """
    Returns the maximal schemas for server-driven CICD, empty since if there arent
    any there is nothing to prune
    """
    return Schemas.create()


##### 1) init the cicd #####


def cicd_init(
    opendapi_config: OpenDAPIConfig,
    change_trigger_event: ChangeTriggerEvent,
    kwargs: dict,
    *,
    should_write_cicd_initialized_file: bool = True,
) -> Tuple[str, dict]:
    """
    Initialize the DAPI server-driven CICD
    """
    print_cli_output(
        "Initializing DAPI server-driven CICD...",
    )
    dapi_server_config = construct_dapi_server_config(kwargs, opendapi_config)
    dapi_requests = DAPIRequests(
        dapi_server_config=dapi_server_config,
        trigger_event=change_trigger_event,
    )
    cicd_location_id, s3_upload_data = dapi_requests.cicd_get_cicd_location_id()
    if should_write_cicd_initialized_file:
        write_cicd_initialized_file(
            {
                "cicd_location_id": cicd_location_id,
                "base_commit_sha": change_trigger_event.before_change_sha,
                "head_commit_sha": change_trigger_event.after_change_sha,
                "head_commit_sha_timestamp": change_trigger_event.after_change_sha_timestamp,
                "opendapi_config": opendapi_config.get_serialized(),
            }
        )
    print_cli_output(
        f"Finished initializing DAPI server-driven CICD with CICD Location ID: {cicd_location_id}",
        color="green",
    )
    return cicd_location_id, s3_upload_data


##### 2) collect files #####


def collect_collected_files(  # pylint: disable=too-many-arguments
    opendapi_config: OpenDAPIConfig,
    change_trigger_event: ChangeTriggerEvent,
    commit_type: CommitType,
    runtime_skip_generation: bool,
    dbt_skip_generation: bool,
    minimal_schemas: Schemas,
    runtime: str,
    commit_already_checked_out: bool,
    kwargs: dict,
):
    """
    Collects the DAPI files for the given runtime at the specified commit
    """
    if change_trigger_event.where != "local" and not missing_dapi_file_exists():
        print_cli_output(
            "Fetching possible missing DAPI files from server...",
            color="yellow",
        )
        dapi_server_config = construct_dapi_server_config(kwargs, opendapi_config)
        dapi_requests = DAPIRequests(
            dapi_server_config=dapi_server_config,
            trigger_event=change_trigger_event,
        )
        missing_dapis_by_filepath = dapi_requests.cicd_get_missing_dapis()
        write_missing_dapis_to_cache(missing_dapis_by_filepath)
        print_cli_output(
            "Successfully fetched possible missing DAPI files from server",
            color="green",
        )

    commit_sha = (
        None
        if commit_type is CommitType.CURRENT
        else change_trigger_event.commit_type_to_sha(commit_type)
    )
    state_str = (
        f"{commit_type.value} commit: {commit_sha}" if commit_sha else "current state"
    )
    print_cli_output(
        (
            "Accumulating DAPI files for your integrations per "
            f"`opendapi.config.yaml` configuration at {state_str}"
            f" for runtime {runtime}"
        ),
        color="green",
    )

    opendapi_config.assert_runtime_exists(runtime)

    metrics_tags = {"org_name": opendapi_config.org_name_snakecase}
    with Timer(dist_key=LogDistKey.COLLECT_FILES, tags=metrics_tags):

        print_cli_output(
            f"Tackling {state_str}...",
            color="yellow",
        )
        collected_files, errors = collect_and_validate_cached(
            opendapi_config=opendapi_config,
            minimal_schemas=minimal_schemas,
            runtime=runtime,
            change_trigger_event=change_trigger_event,
            commit_type=commit_type,
            commit_already_checked_out=commit_already_checked_out,
            # integration specific flags
            runtime_skip_generation=runtime_skip_generation,
            dbt_skip_generation=dbt_skip_generation,
        )
        if errors:
            pretty_print_errors(errors)
            # fails with exit code 1 - meaning it blocks merging - but as a ClickException
            # it does not go to sentry, which is appropriate, as this is not an error condition
            raise click.ClickException("Encountered one or more validation errors")

        return collected_files


##### 3) locally persist files #####


def locally_persist_collected_files(
    collected_files: Dict[OpenDAPIEntity, Dict[str, CollectedFile]],
    opendapi_config: OpenDAPIConfig,
    commit_type: CommitType,
    runtime: str,
):
    """
    Persists the collected files to the filesystem, to be loaded later
    """
    metrics_tags = {"org_name": opendapi_config.org_name_snakecase}
    with Timer(dist_key=LogDistKey.PERSIST_COLLECTED_FILES, tags=metrics_tags):
        print_cli_output(
            "Persisting to filesystem...",
            color="yellow",
        )
        collected_files_tmp_dump(commit_type, collected_files, runtime)
        print_cli_output(
            f"Successfully persisted DAPI files for your integrations for runtime {runtime}",
            color="green",
        )


##### 4) load locally persisted files #####


def load_locally_persisted_collected_files(
    opendapi_config: OpenDAPIConfig,
    commit_type: CommitType,
    runtime: str,
):
    """
    Loads the collected files from the filesystem
    """
    opendapi_config.assert_runtime_exists(runtime)

    print_cli_output(
        (
            f"Loading persisted DAPI files for your integrations for runtime {runtime} "
            f"at commit type {commit_type.value}..."
        ),
        color="yellow",
    )

    metrics_tags = {"org_name": opendapi_config.org_name_snakecase}
    with Timer(dist_key=LogDistKey.LOAD_COLLECTED_FILES, tags=metrics_tags):
        collected_files = collected_files_tmp_load(commit_type, runtime)

    print_cli_output(
        (
            f"Successfully loaded persisted DAPI files for your integrations for runtime {runtime} "
            f"at commit type {commit_type.value}"
        ),
        color="green",
    )
    return collected_files


##### 5) get s3 upload data #####


def cicd_get_s3_upload_data(
    cicd_location_id: str,
    change_trigger_event: ChangeTriggerEvent,
    opendapi_config: OpenDAPIConfig,
    kwargs: dict,
) -> dict:
    """
    Get the s3 upload data for the given cicd location id
    """
    dapi_server_config = construct_dapi_server_config(kwargs, opendapi_config)
    dapi_requests = DAPIRequests(
        dapi_server_config=dapi_server_config,
        trigger_event=change_trigger_event,
    )
    return dapi_requests.cicd_get_s3_upload_data(
        cicd_location_id=cicd_location_id,
    )


##### 6) persist files to server #####


def cicd_persist_files(  # pylint: disable=too-many-arguments, too-many-locals
    base_collected_files: Dict[OpenDAPIEntity, Dict[str, CollectedFile]],
    head_collected_files: Dict[OpenDAPIEntity, Dict[str, CollectedFile]],
    change_trigger_event: ChangeTriggerEvent,
    opendapi_config: OpenDAPIConfig,
    s3_upload_data: dict,
    runtime: str,
    kwargs: dict,
):
    """
    Posts the collected files to the DAPI  server for server-driven CICD
    """
    metrics_tags = {"org_name": opendapi_config.org_name_snakecase}
    with Timer(dist_key=LogDistKey.SERVER_SYNC_TO_SERVER, tags=metrics_tags):
        dapi_server_config = construct_dapi_server_config(kwargs, opendapi_config)
        dapi_requests = DAPIRequests(
            dapi_server_config=dapi_server_config,
            trigger_event=change_trigger_event,
        )

        print_cli_output(
            f"Syncing with DAPI Server for runtime {runtime}...",
            color="yellow",
        )

        total_filepaths = {
            fp
            for entity_collected in (base_collected_files, head_collected_files)
            for filepaths in entity_collected.values()
            for fp in filepaths
        }

        with click.progressbar(length=len(total_filepaths)) as progressbar:

            def _notify_progress(progress: int):  # pragma: no cover
                progressbar.update(progress)
                print_cli_output(
                    (
                        f"\nFinished {round(progressbar.pct * 100)}% with"
                        f"{progressbar.format_eta()} remaining"
                    ),
                    color="green",
                    bold=True,
                )

            dapi_requests.cicd_persist_files(
                s3_upload_data=s3_upload_data,
                base_collected_files=base_collected_files,
                head_collected_files=head_collected_files,
                runtime=runtime,
                notify_function=_notify_progress,
            )

        print_cli_output(
            (
                "Successfully synced DAPI files for your integrations to DAPI Server "
                f"for runtime {runtime}"
            ),
            color="green",
        )


##### 7) start server driven CICD #####


def cicd_start(
    call_cicd_start: Callable[[DAPIRequests, dict], None],
    cicd_location_id: str,
    opendapi_config: OpenDAPIConfig,
    change_trigger_event: ChangeTriggerEvent,
    cicd_integration: CICDIntegration,
    runner_run_info: dict,
    kwargs: dict,
):
    """
    Start the DAPI server-driven CICD
    """
    dapi_server_config = construct_dapi_server_config(kwargs, opendapi_config)
    dapi_requests = DAPIRequests(
        dapi_server_config=dapi_server_config,
        trigger_event=change_trigger_event,
    )
    metadata_file = {
        "runtimes": opendapi_config.runtime_names,
        "run_info": {
            "version": f"opendapi-{version('opendapi')}",
            "integration_mode": dapi_server_config.woven_integration_mode.value,
            "repo_being_configured": dapi_server_config.repo_being_configured,
            "integration": cicd_integration.value,
            "register_on_merge_to_mainline": (
                dapi_server_config.register_on_merge_to_mainline
            ),
            "mainline_branch_name": dapi_server_config.mainline_branch_name,
            **runner_run_info,
        },
        # NOTE: after landing this should be removed, as its a relic
        #       of the previous impl
        "opendapi_config": opendapi_config.config,
        "change_trigger_event": change_trigger_event.as_dict,
        "cicd_location_id": cicd_location_id,
    }
    call_cicd_start(dapi_requests, metadata_file)
    print_cli_output(
        "Successfully started DAPI server-driven CICD",
        color="green",
    )
    cleanup_tmp_state(opendapi_config)
    cleanup_opendapi_cache()


##### LOCAL HELPERS #####


def write_locally(
    opendapi_config: OpenDAPIConfig,
    base_collected_files: Dict[OpenDAPIEntity, Dict[str, CollectedFile]],
    current_collected_files: Dict[OpenDAPIEntity, Dict[str, CollectedFile]],
    kwargs: dict,
):
    """Writing portion of generate-like commands"""
    # actually write
    always_write = kwargs.get("always_write_generated_dapis", False)
    metrics_tags = {"org_name": opendapi_config.org_name_snakecase}

    print_cli_output(
        "Writing DAPI files for your integrations...",
        color="yellow",
    )

    with Timer(dist_key=LogDistKey.WRITE_FILES, tags=metrics_tags):
        for entity, collected_files in current_collected_files.items():
            writer_cls = get_writer_for_entity(entity)
            writer = writer_cls(
                root_dir=opendapi_config.root_dir,
                collected_files=collected_files,
                override_config=opendapi_config,
                base_collected_files=base_collected_files.get(entity),
                always_write=always_write,
            )
            written, skipped = writer.write_files()
            print_cli_output(
                f"{entity.value}: {len(written)} written, {len(skipped)} skipped",
                color="green",
            )

    print_cli_output(
        "Successfully generated DAPI files for your integrations",
        color="green",
    )
    cleanup_tmp_state(opendapi_config)


def reconcile_collected_files_across_runtimes(
    opendapi_config: OpenDAPIConfig,
    collected_files_by_runtime: Dict[
        str, Dict[OpenDAPIEntity, Dict[str, CollectedFile]]
    ],
) -> Dict[OpenDAPIEntity, Dict[str, CollectedFile]]:
    """
    Reconcile the collected files for the runtimes
    """

    print_cli_output(
        "Reconciling persisted DAPI files for your integrations...",
        color="yellow",
    )

    entity_to_filepath_to_runtime_to_collected_file = defaultdict(
        lambda: defaultdict(dict)
    )
    for runtime in opendapi_config.runtime_names:
        collected_files = collected_files_by_runtime[runtime]

        for entity, filepath_to_collected_file in collected_files.items():
            for filepath, collected_file in filepath_to_collected_file.items():
                entity_to_filepath_to_runtime_to_collected_file[entity][filepath][
                    runtime
                ] = collected_file

    reconciled_collected_files = defaultdict(dict)
    for (
        entity,
        filepath_to_runtime_to_collected_file,
    ) in entity_to_filepath_to_runtime_to_collected_file.items():
        for (
            filepath,
            runtime_to_collected_file,
        ) in filepath_to_runtime_to_collected_file.items():
            reconciled = None
            for runtime, collected_file in runtime_to_collected_file.items():
                reconciled = collected_file.reconcile(reconciled)
            reconciled_collected_files[entity][filepath] = reconciled

    print_cli_output(
        "Successfully reconciled persisted DAPI files for your integrations",
        color="green",
    )
    return reconciled_collected_files
