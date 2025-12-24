# pylint: disable=too-many-locals
""" "Adapter to interact with the DAPI Server."""
from __future__ import annotations

import asyncio
import io
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from importlib.metadata import version
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar
from urllib.parse import urljoin

import aiohttp
import requests

from opendapi.adapters.git import ChangeTriggerEvent
from opendapi.config import OpenDAPIConfig
from opendapi.defs import HTTPMethod, IntegrationMode, OpenDAPIEntity
from opendapi.logging import LogDistKey, Timer, logger, sentry_sdk
from opendapi.utils import (
    async_backoff_retry,
    create_session_with_retries,
    dump_dict_to_yaml_str,
    make_api_w_query_and_body,
)
from opendapi.validators.defs import CollectedFile, OpenDAPIEntityCICDMetadata

TOTAL_RETRIES = 5
RETRY_BACKOFF_FACTOR = 10

CICD_PERSISTED_FILE_SUFFIX = ".cicd.yaml"
OPENDAPI_FILEPATHS_RUNTIME_BLUEPRINT = "{runtime}/opendapi_filepaths.yaml"

T = TypeVar("T")


@dataclass
class DAPIServerConfig:
    """Configuration for the DAPI Server."""

    server_host: str
    api_key: str
    mainline_branch_name: str
    woven_integration_mode: IntegrationMode
    register_on_merge_to_mainline: bool = True
    woven_configuration: str | None = None

    @property
    def repo_being_configured(self) -> bool:
        """Check if the repo is configured."""
        return self.woven_configuration == "in_progress"


class CICDIntegration(Enum):
    """Enum for CICD integrations."""

    GITHUB_BUILDKITE = "github_buildkite"
    GITHUB_GITHUB = "github_github"


class DAPIServerRequestType(Enum):
    """Enum for DAPI Server Request Types."""

    CLIENT_CONFIG = "/v1/config/client/opendapi"
    CLIENT_FEATURE_FLAGS = "/v1/config/client/opendapi/feature_flags"
    CICD_GET_CICD_LOCATION_ID = "/v2/cicd/cicd_location_id"
    GITHUB_BUILDKITE_CICD_START = "/v2/cicd/start/github_buildkite"
    GITHUB_GITHUB_CICD_START = "/v2/cicd/start/github_github"
    CICD_GET_PRESIGNED_LINK_BLUEPRINT = "/v2/cicd/files/persist/presigned"
    CICD_GET_MISSING_DAPIS = "/v2/cicd/dapi/missing"


class DAPIRequests:
    """Class to handle requests to the DAPI Server."""

    def __init__(
        self,
        dapi_server_config: DAPIServerConfig,
        trigger_event: ChangeTriggerEvent,
        opendapi_config: Optional[OpenDAPIConfig] = None,
        error_msg_handler: Optional[Callable[[str], None]] = None,
        error_exception_cls: Optional[Type[Exception]] = None,
        txt_msg_handler: Optional[Callable[[str], None]] = None,
        markdown_msg_handler: Optional[Callable[[str], None]] = None,
    ):  # pylint: disable=too-many-arguments
        self.dapi_server_config = dapi_server_config
        self.opendapi_config = opendapi_config
        self.trigger_event = trigger_event
        self.error_msg_handler = error_msg_handler
        self.error_exception_cls = error_exception_cls or Exception
        self.txt_msg_handler = txt_msg_handler
        self.markdown_msg_handler = markdown_msg_handler

        self.session = create_session_with_retries(
            total_retries=TOTAL_RETRIES,
            backoff_factor=RETRY_BACKOFF_FACTOR,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
            print_retries=True,
        )

    def get_client_config_from_server(self) -> dict:
        """Get the config from the DAPI Server."""
        response, _ = self.raw_send_request_to_dapi_server(
            request_path=DAPIServerRequestType.CLIENT_CONFIG.value,
            method=HTTPMethod.GET,
        )
        response.raise_for_status()
        return response.json()

    def get_client_feature_flags_from_server(
        self,
        feature_flag_names: List[str],
    ) -> dict:
        """Get the feature flags from the DAPI Server."""
        response, _ = self.raw_send_request_to_dapi_server(
            request_path=DAPIServerRequestType.CLIENT_FEATURE_FLAGS.value,
            method=HTTPMethod.POST,
            query_params=None,
            body_json={
                "feature_flag_names": feature_flag_names,
                "client_context": self.build_client_context(
                    self.dapi_server_config, self.trigger_event
                ),
            },
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def build_client_context(
        dapi_server_config: DAPIServerConfig,
        trigger_event: ChangeTriggerEvent,
    ) -> dict:
        """Build the client context."""
        return {
            "meta": {
                "type": "opendapi",
                "version": f"opendapi-{version('opendapi')}",
                "integration_mode": dapi_server_config.woven_integration_mode.value,
                "repo_being_configured": dapi_server_config.repo_being_configured,
            },
            "change_trigger_event": {
                "source": trigger_event.integration_type,
                "repository": trigger_event.repo_full_name,
                "where": trigger_event.where,
                "event_type": trigger_event.event_type,
                "before_change_sha": trigger_event.before_change_sha,
                "after_change_sha": trigger_event.after_change_sha,
                "repo_html_url": trigger_event.repo_html_url,
                "pull_request_number": trigger_event.pull_request_number,
                "pull_request_link": trigger_event.pull_request_link,
                "branch": trigger_event.branch,
            },
        }

    def raw_send_request_to_dapi_server(
        self,
        request_path: str,
        method: HTTPMethod,
        query_params: Optional[dict] = None,
        body_json: Optional[dict] = None,
    ) -> Tuple[requests.Response, Dict]:
        """Send a request to the DAPI Server."""
        headers = {
            "Content-Type": "application/json",
            "X-DAPI-Server-API-Key": self.dapi_server_config.api_key,
        }
        # measure the time it takes to get a response from the server in milliseconds
        metrics_tags = {
            "request_path": request_path,
            "org_name": self.opendapi_config
            and self.opendapi_config.org_name_snakecase,
        }

        with Timer(LogDistKey.ASK_DAPI_SERVER) as _timer:
            response, _ = make_api_w_query_and_body(
                urljoin(self.dapi_server_config.server_host, request_path),
                headers=headers,
                query_params=query_params,
                body_json=body_json,
                method=method,
                timeout=60,
                req_session=self.session,
            )
            metrics_tags["status_code"] = response.status_code
            _timer.set_tags(metrics_tags)

        return response, metrics_tags

    def _handle_api_error(self, request_path: str, status_code: int) -> None:
        """Handle an error message."""
        msg = f"Something went wrong! API failure with {status_code} for {request_path}"
        if self.error_msg_handler:
            self.error_msg_handler(msg)
        raise self.error_exception_cls(msg)

    ##### 1) Get CICD Location ID #####

    def cicd_get_cicd_location_id(self) -> Tuple[str, dict]:
        """Get the S3 prefix for the CI/CD."""

        if not self.trigger_event.after_change_sha_timestamp:  # pragma: no cover
            raise ValueError("head_commit_sha_timestamp is required")

        request_path = DAPIServerRequestType.CICD_GET_CICD_LOCATION_ID.value
        response, _ = self.raw_send_request_to_dapi_server(
            request_path=request_path,
            query_params={
                "repo_name": self.trigger_event.repo_full_name,
                "head_commit_sha": self.trigger_event.after_change_sha,
                "head_commit_sha_timestamp": self.trigger_event.after_change_sha_timestamp,
            },
            method=HTTPMethod.GET,
        )
        if response.status_code >= 400:
            self._handle_api_error(request_path, response.status_code)
        response_json = response.json()
        return response_json["cicd_location_id"], response_json["s3_upload_data"]

    ##### 2) Persisting Files to S3 #####

    def cicd_get_s3_upload_data(
        self,
        cicd_location_id: str,
    ) -> dict:
        """Get the S3 upload data for the CI/CD."""
        request_path = DAPIServerRequestType.CICD_GET_PRESIGNED_LINK_BLUEPRINT.value
        response, _ = self.raw_send_request_to_dapi_server(
            request_path=request_path,
            query_params={
                "cicd_location_id": cicd_location_id,
            },
            method=HTTPMethod.GET,
        )
        if response.status_code >= 400:
            self._handle_api_error(request_path, response.status_code)
        return response.json()["s3_upload_data"]

    async def __upload_to_s3(
        self,
        filename: str,
        file_obj: io.BytesIO,
        s3_upload_data: Dict[str, str],
        session: aiohttp.ClientSession,
        notify_function: Optional[Callable[[int], None]] = lambda _: None,
    ) -> None:

        s3_upload_data["fields"]["key"] = s3_upload_data["fields"]["key"].replace(
            "${filename}", filename
        )

        form = aiohttp.FormData()
        # form fields for the policy and signature to then be verified by AWS
        # that the signature matches and the policy was not tampered with
        for key, value in s3_upload_data["fields"].items():
            form.add_field(key, value)
        # actually include the file in the form
        form.add_field(
            "file",
            value=file_obj,
            filename=filename,
            content_type=s3_upload_data["fields"]["Content-Type"],
        )

        async def _post():
            async with session.post(s3_upload_data["url"], data=form) as response:
                if response.status == 204:
                    notify_function(1)
                    return
                error_text = await response.text()
                raise self.error_exception_cls(
                    f"Failed to upload to S3: {response.status} - {error_text}"
                )

        await async_backoff_retry(
            _post,
            max_attempts=3,
            initial_backoff_seconds=1,
            exceptions_to_catch=(Exception,),
        )

    async def _cicd_upload_to_s3(
        self,
        runtime: str,
        s3_upload_data: Dict[str, str],
        cicd_metadata: OpenDAPIEntityCICDMetadata,
        session: aiohttp.ClientSession,
        notify_function: Optional[Callable[[int], None]] = lambda _: None,
    ) -> None:
        """Upload the CI/CD files to S3."""

        s3_upload_data = deepcopy(s3_upload_data)

        filename = (
            f"{runtime}/{cicd_metadata.entity.value}/"
            f"{cicd_metadata.filepath}{CICD_PERSISTED_FILE_SUFFIX}"
        )
        file_obj = io.BytesIO(
            dump_dict_to_yaml_str(cicd_metadata.for_server).encode("utf-8")
        )
        return await self.__upload_to_s3(
            filename, file_obj, s3_upload_data, session, notify_function
        )

    def cicd_persist_files(
        self,
        s3_upload_data: Dict[str, str],
        base_collected_files: Dict[OpenDAPIEntity, Dict[str, CollectedFile]],
        head_collected_files: Dict[OpenDAPIEntity, Dict[str, CollectedFile]],
        runtime: str,
        notify_function: Optional[Callable[[int], None]] = None,
    ) -> Dict[OpenDAPIEntity, List[str]]:
        """Persist the CI/CD files with the DAPI Server."""
        # first, create the CICDMetadata objects

        async def _cicd_persist_files():
            total_entities = base_collected_files.keys() | head_collected_files.keys()
            opendapi_file_metadata: List[OpenDAPIEntityCICDMetadata] = []
            for entity in total_entities:
                bc_raw = base_collected_files.get(entity, {})
                bc = {
                    collected_file.server_filepath: collected_file
                    for collected_file in bc_raw.values()
                }
                hc_raw = head_collected_files.get(entity, {})
                hc = {
                    collected_file.server_filepath: collected_file
                    for collected_file in hc_raw.values()
                }
                total_filepaths = bc.keys() | hc.keys()
                for filepath in total_filepaths:
                    opendapi_file_metadata.append(
                        OpenDAPIEntityCICDMetadata(
                            entity=entity,
                            filepath=filepath,
                            base_collect=bc.get(filepath),
                            head_collect=hc.get(filepath),
                            integration_mode=self.dapi_server_config.woven_integration_mode,
                        )
                    )

            # then, upload the CICD files to S3 in parallel
            # NOTE default limits are 100 connections in the pool and 100 per host
            #      - we can bump that if we want, but seems like an okay starting point..
            async with aiohttp.ClientSession() as session:
                # for things like registration, we want all of the files
                filepath_by_entity = defaultdict(list)
                # but, for most CICD runs that are PR focused, we only want the the changed dapis
                # and then all of the other files
                minimal_cicd_filepath_by_entity = defaultdict(list)
                tasks = []
                for cicd_metadata in opendapi_file_metadata:
                    tasks.append(
                        self._cicd_upload_to_s3(
                            runtime,
                            s3_upload_data,
                            cicd_metadata,
                            session,
                            notify_function,
                        )
                    )
                    filepath_by_entity[cicd_metadata.entity].append(
                        cicd_metadata.filepath
                    )
                    if cicd_metadata.required_for_minimal_cicd:
                        minimal_cicd_filepath_by_entity[cicd_metadata.entity].append(
                            cicd_metadata.filepath
                        )

                filename = OPENDAPI_FILEPATHS_RUNTIME_BLUEPRINT.format(runtime=runtime)
                entity_to_filepaths = {
                    entity.value: filepaths
                    for entity, filepaths in filepath_by_entity.items()
                }
                minimal_cicd_entity_to_filepaths = {
                    entity.value: filepaths
                    for entity, filepaths in minimal_cicd_filepath_by_entity.items()
                }
                file_obj = io.BytesIO(
                    dump_dict_to_yaml_str(
                        {
                            "runtime": runtime,
                            "entity_to_filepaths": entity_to_filepaths,
                            "minimal_cicd_entity_to_filepaths": minimal_cicd_entity_to_filepaths,
                            # NOTE: after landing this should be removed, as its a relic
                            #       of the previous impl.
                            # NOTE: when we do this work with dapi server to drop v2 stuff probably...
                            **{
                                entity.value: filepaths
                                for entity, filepaths in filepath_by_entity.items()
                                if entity is not OpenDAPIEntity.OPENDAPI_CONFIG
                            },
                            "minimal_cicd_required_filepaths": {
                                entity.value: filepaths
                                for entity, filepaths in minimal_cicd_filepath_by_entity.items()
                                if entity is not OpenDAPIEntity.OPENDAPI_CONFIG
                            },
                        }
                    ).encode("utf-8")
                )
                tasks.append(
                    self.__upload_to_s3(filename, file_obj, s3_upload_data, session)
                )

                try:
                    # already cancels non completed tasks
                    await asyncio.gather(*tasks)
                except Exception as e:  # pylint: disable=broad-except
                    sentry_sdk.capture_exception(e)
                    raise self.error_exception_cls(
                        "There was an error persisted files for CICD. "
                        "Please rerun the workflow to try again."
                    ) from e

            return filepath_by_entity

        return asyncio.run(_cicd_persist_files())

    ##### 3) CICD Start #####

    def _github_repo_cicd_start(
        self,
        cicd_location_id: str,
        metadata_file: Dict[str, Any],
        request_path: str,
        runner_params: Dict[str, Any],
    ) -> str:
        """
        Returns a common payload for all github repo operations
        """

        response, _ = self.raw_send_request_to_dapi_server(
            request_path=request_path,
            query_params={
                # global query
                "cicd_location_id": cicd_location_id,
            },
            body_json={
                # global body
                "metadata": metadata_file,
                "version": f"opendapi-{version('opendapi')}",
                "integration_mode": self.dapi_server_config.woven_integration_mode.value,
                # runner body
                **runner_params,
                # github repo body
                "event": self.trigger_event.event_type,
                "branch": self.trigger_event.branch,
                "base_commit_sha": self.trigger_event.before_change_sha,
                "head_commit_sha": self.trigger_event.after_change_sha,
                "pr_link": self.trigger_event.pull_request_link,
                # default global body
                "logs": logger.get_logs(),
            },
            method=HTTPMethod.POST,
        )

        if response.status_code >= 400:
            self._handle_api_error(
                request_path,
                response.status_code,
            )

        return response.json()["woven_cicd_id"]

    def cicd_start_github_buildkite(
        self,
        cicd_location_id: str,
        build_id: str,
        build_number: int,
        metadata_file: Dict[str, Any],
    ) -> str:
        """Notify the DAPI Server that the GitHub CI/CD has started."""
        return self._github_repo_cicd_start(
            cicd_location_id,
            metadata_file,
            DAPIServerRequestType.GITHUB_BUILDKITE_CICD_START.value,
            {
                "build_id": build_id,
                "build_number": build_number,
                # NOTE: this is not exact - if we could get it we should use that.
                #       but this is here so that successes come after failures and so
                #       we can sort successful runs
                "build_started_at": datetime.now(timezone.utc).isoformat(),
                "pipeline_name": self.trigger_event.workflow_name,
            },
        )

    def cicd_start_github_github(
        self,
        cicd_location_id: str,
        run_id: str,
        run_attempt: int,
        run_number: int,
        metadata_file: Dict[str, Any],
    ) -> str:
        """Notify the DAPI Server that the GitHub CI/CD has started."""
        return self._github_repo_cicd_start(
            cicd_location_id,
            metadata_file,
            DAPIServerRequestType.GITHUB_GITHUB_CICD_START.value,
            {
                "run_id": run_id,
                "run_attempt": run_attempt,
                "run_number": run_number,
                # NOTE: this is not exact - if we could get it we should use that.
                #       but this is here so that successes come after failures and so
                #       we can sort successful runs
                "run_started_at": datetime.now(timezone.utc).isoformat(),
                "workflow_name": self.trigger_event.workflow_name,
            },
        )

    ##### Missing DAPI Helper #####

    def cicd_get_missing_dapis(self) -> dict[str, dict]:
        """
        Get the missing DAPI files for the CICD run.

        NOTE: this DOES NOT prefix with the root dir
        """
        request_path = DAPIServerRequestType.CICD_GET_MISSING_DAPIS.value
        response, _ = self.raw_send_request_to_dapi_server(
            request_path=request_path,
            method=HTTPMethod.GET,
            query_params={
                "repo_name": self.trigger_event.repo_full_name,
            },
        )
        if response.status_code >= 400:
            self._handle_api_error(request_path, response.status_code)

        return response.json()["missing_dapi_dicts_by_filepath"]
