"""DBT Cloud mixin for dapi_validator"""

# pylint: disable=too-few-public-methods, too-many-locals, too-many-arguments
# pylint: disable=too-many-instance-attributes

from __future__ import annotations

import json
import os
import threading
import time
from copy import deepcopy
from logging import Logger
from typing import Callable, Dict, List, Optional, Set, Tuple, Type, TypeVar
from urllib.parse import urljoin

import requests

from opendapi.cli.common import (
    highlight_message,
    print_cli_output,
)
from opendapi.defs import CommitType
from opendapi.logging import logger
from opendapi.utils import (
    HTTPMethod,
    create_session_with_retries,
    make_api_w_query_and_body,
)

DBT_CLOUD_RUN_STATUSES = {
    "queued": 1,
    "starting": 2,
    "running": 3,
    "success": 10,  # means the job has completed
    "error": 20,
    "cancelled": 30,
}
OPENDAPI_DBT_CLOUD_JOB_NAME = "opendapi_ci_fast_generate_docs"
OPENDAPI_JOB_SUFFIX_TRIGGER = "trigger_on_opendapi_ci_pass"
DEFAULT_DBT_CLOUD_RUN_LOOKUP_MAX_ITERATIONS = 5

_thread_local = threading.local()


def _get_session() -> requests.Session:  # pragma: no cover
    if not hasattr(_thread_local, "session"):
        _thread_local.session = create_session_with_retries(
            total_retries=2,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
        )
    return _thread_local.session


DBTCloudProjectBaseType = TypeVar(  # pylint: disable=invalid-name
    "DBTCloudProjectBaseType", bound="DBTCloudProjectBase"
)


class DBTCloudProjectBase:
    """DBT Cloud project"""

    _get_session: Callable[[], requests.Session] = _get_session
    _logger: Logger = NotImplemented
    _log_text: Callable[[str], None] = lambda _: None

    def __init__(
        self,
        dbt_cloud_url: str,
        api_key: str,
        project_id: int,
        account_id: int,
        repo_name: str,
        project_name: str,
        subdirectory: str,
        prod_docs_job_id: Optional[int] = None,
        ensure_opendapi_job_exists: bool = True,
    ):
        self.dbt_cloud_url = dbt_cloud_url
        self.api_key = api_key
        self.project_id = project_id
        self.account_id = account_id
        self.repo_name = repo_name
        self.project_name = project_name
        self._ci_job_id = self._get_opendapi_job_id()

        # asserts that the opendapi job exists
        if ensure_opendapi_job_exists:
            _ = self.ci_job_id

        self.subdirectory = subdirectory
        self.prod_docs_job_id = prod_docs_job_id

    @property
    def is_integrated_to_ci(self) -> bool:
        """Whether the project is integrated to CI"""
        return self._ci_job_id is not None  # pragma: no cover

    @property
    def ci_job_id(self) -> int:
        """Get the ci job id"""
        if self._ci_job_id is None:
            raise RuntimeError(
                f"No opendapi job found for the given project {self.project_id}"
            )
        return self._ci_job_id

    @property
    def unique_name(self):
        """Unique key."""
        name = self.repo_name
        if self.subdirectory:
            name += f"/{self.subdirectory}"
        return name

    @property
    def is_generating_docs(self) -> bool:
        """Whether the project is generating docs"""
        return self.prod_docs_job_id is not None  # pragma: no cover

    @staticmethod
    def build_run_html_url(run: Dict) -> str:
        """Build the HTML URL for a run"""
        return urljoin(
            os.environ["DAPI_DBT_CLOUD_URL"],
            f"/deploy/{run['account_id']}"
            f"/projects/{run['project_id']}/runs/{run['id']}",
        )

    def get_custom_schema(
        self, github_pr_number: Optional[int], commit_type: CommitType
    ) -> str:
        """Get the custom schema"""
        if github_pr_number:
            # not including commit_sha in hopes that it will be reused
            # NOTE: for PRs any schema that has prefix `dbt_cloud_pr_JOB_ID_PR_NUMBER`
            #       will be cleaned up by dbt cloud once the PR is closed.
            return (
                f"dbt_cloud_pr_{self.ci_job_id}_{github_pr_number}_{commit_type.value}"
            )

        # update this when we are able to run for main branch
        raise RuntimeError("PR number not supplied for CI job")  # pragma: no cover

    @classmethod
    def dbt_cloud_request(
        cls,
        dbt_cloud_url: str,
        api_key: str,
        uri_path: str,
        http_method: HTTPMethod = HTTPMethod.GET,
        body: Optional[Dict] = None,
        params: Optional[Dict] = None,
        content_type: str = "application/json",
    ) -> requests.Response:
        """Make a request to the DBT Cloud API"""
        headers = {
            "Content-Type": content_type,
            "Authorization": f"Token {api_key}",
        }

        response, _ = make_api_w_query_and_body(
            url=urljoin(dbt_cloud_url, uri_path),
            headers=headers,
            body_json=body,
            query_params=params,
            method=http_method,
            timeout=10,
            req_session=cls._get_session(),
        )

        response.raise_for_status()
        return response

    def _dbt_cloud_request(
        self,
        uri_path: str,
        http_method: HTTPMethod = HTTPMethod.GET,
        body: Optional[Dict] = None,
        params: Optional[Dict] = None,
        content_type: str = "application/json",
    ) -> requests.Response:
        """Make a request to the DBT Cloud API"""
        return self.dbt_cloud_request(
            self.dbt_cloud_url,
            self.api_key,
            uri_path,
            http_method,
            body,
            params,
            content_type,
        )

    @classmethod
    def _validate_json_response(cls, response: requests.Response) -> None:
        response = response.json()
        if response["status"]["code"] != 200 or not response["status"]["is_success"]:
            cls._logger.error(  # pylint: disable=no-member
                "DBT Cloud API request failed: %s", response
            )
            raise RuntimeError("DBT Cloud API request failed")

    @classmethod
    def dbt_cloud_api_request(
        cls,
        dbt_cloud_url: str,
        api_key: str,
        uri_path: str,
        http_method: HTTPMethod = HTTPMethod.GET,
        body: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """Make a request to the DBT Cloud API"""
        response = cls.dbt_cloud_request(
            dbt_cloud_url, api_key, uri_path, http_method, body, params
        )
        cls._validate_json_response(response)
        return response.json()["data"]

    def _dbt_cloud_api_request(
        self,
        uri_path: str,
        http_method: HTTPMethod = HTTPMethod.GET,
        body: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """Make a request to the DBT Cloud API, used by instances"""
        return self.dbt_cloud_api_request(
            self.dbt_cloud_url,
            self.api_key,
            uri_path,
            http_method,
            body,
            params,
        )

    def _get_ci_jobs(
        self,
        account_id: int,
        project_id: int,
        name__icontains: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        base_url = f"/api/v2/accounts/{account_id}/jobs"
        params = {
            "project_id": project_id,
            "state": 1,
            **({"name__icontains": name__icontains} if name__icontains else {}),
            "limit": limit,
        }
        return [
            job
            for job in self._dbt_cloud_api_request(base_url, params=params)
            if job["job_type"] == "ci"
        ]

    def _get_opendapi_job_id(self) -> int | None:
        """Get the opendapi job id for a given dbt cloud project and commit sha"""
        response = self._get_ci_jobs(
            self.account_id, self.project_id, OPENDAPI_DBT_CLOUD_JOB_NAME, 5
        )
        try:
            return next(
                (
                    job["id"]
                    for job in response
                    if job["name"] == OPENDAPI_DBT_CLOUD_JOB_NAME
                ),
            )
        except StopIteration:
            return None

    def get_latest_ci_run(
        self,
        match_git_sha: Optional[str] = None,
        statuses: Set[int] = frozenset({DBT_CLOUD_RUN_STATUSES["success"]}),
        job_id: Optional[int] = None,
        # we opt for job names since we can check for them earlier in the flow
        allowed_job_names_without_has_docs_generated: Set[str] = frozenset(
            (OPENDAPI_DBT_CLOUD_JOB_NAME,)
        ),
        only_run_ids: Optional[Set[int]] = None,
    ) -> Optional[Dict]:
        """Get latest run of dbt Cloud for a given project, optionally matching git sha or job ID"""
        base_url = f"/api/v2/accounts/{self.account_id}/runs"
        params = {
            "project_id": self.project_id,
            **({"status__in": str(list(statuses))} if statuses else {}),
            # to be used later to filter by PR number
            "include_related": str(["trigger", "job"]),
            "order_by": "-created_at",
            "limit": 100,
            "offset": 0,
        }
        if job_id:
            params["job_definition_id"] = job_id

        match_run = None
        for idx in range(
            os.environ.get(
                "DAPI_DBT_CLOUD_MAX_ITERATIONS",
                DEFAULT_DBT_CLOUD_RUN_LOOKUP_MAX_ITERATIONS,
            )
        ):
            params["offset"] = idx * params["limit"]
            runs = self._dbt_cloud_api_request(base_url, params=params)
            match_run = next(
                (
                    r
                    for r in runs
                    if (
                        # NOTE: there are diff artifacts depending on how it was triggered,
                        #       and rn we can only handle CI, which is why this method
                        #       is ci specific
                        r["job"]["job_type"] == "ci"
                        and (
                            r.get("has_docs_generated")
                            or (
                                r["job"]["name"]
                                in allowed_job_names_without_has_docs_generated
                            )
                            # r["has_docs_generated"] is ONLY present after the run has completed
                            or (
                                r["status"]
                                in {
                                    DBT_CLOUD_RUN_STATUSES["queued"],
                                    DBT_CLOUD_RUN_STATUSES["starting"],
                                    DBT_CLOUD_RUN_STATUSES["running"],
                                }
                                and (
                                    r["trigger"]["generate_docs_override"]
                                    if r["trigger"]["generate_docs_override"]
                                    is not None
                                    else r["job"]["generate_docs"]
                                )
                            )
                        )
                        and (
                            not match_git_sha
                            or (
                                # r["git_sha"] is ONLY present after the run has completed
                                (r["git_sha"] or r["trigger"]["git_sha"])
                                == match_git_sha
                            )
                        )
                        and (only_run_ids is None or r["id"] in only_run_ids)
                    )
                ),
                None,
            )
            if match_run or not runs:
                # End early if no more runs found
                break
        return match_run

    def _download_job_artifact(self, artifact_name: str, job_id: int) -> Dict:
        """Download the artifact from dbt cloud"""
        base_url = f"/api/v2/accounts/{self.account_id}/jobs/{job_id}/artifacts/{artifact_name}"
        content = self._dbt_cloud_request(
            base_url,
            content_type="application/text",
        ).text
        return json.loads(content)

    def _download_run_artifact(self, artifact_name: str, run_id: int) -> Dict:
        """Download the artifact from dbt cloud"""
        base_url = f"/api/v2/accounts/{self.account_id}/runs"
        artifacts_url = f"{base_url}/{run_id}/artifacts/"
        artifact_url = f"{artifacts_url}{artifact_name}"
        content = self._dbt_cloud_request(
            artifact_url,
            content_type="application/text",
        ).text
        return json.loads(content)

    def get_production_catalog(self) -> Optional[dict]:
        """Get the production catalog"""
        try:
            return (
                self._download_job_artifact("catalog.json", self.prod_docs_job_id)
                if self.prod_docs_job_id
                else None
            )
        except requests.RequestException:
            return None

    def get_production_manifest(self) -> Optional[dict]:
        """Get the production manifest"""
        try:
            return (
                self._download_job_artifact("manifest.json", self.prod_docs_job_id)
                if self.prod_docs_job_id
                else None
            )
        except requests.RequestException:
            return None

    def get_production_catalog_manifest(self) -> Tuple[Optional[dict], Optional[dict]]:
        """Get the production catalog and manifest"""
        return (
            self.get_production_catalog(),
            self.get_production_manifest(),
        )

    def get_catalog_for_ci_run(self, run_id: int) -> dict:
        """Get the catalog for a given ci run"""
        return self._download_run_artifact("catalog.json", run_id)

    def get_manifest_for_ci_run(self, run_id: int) -> dict:
        """Get the manifest for a given ci run"""
        return self._download_run_artifact("manifest.json", run_id)

    @staticmethod
    def merge_catalogs(source: Dict, target: Optional[Dict] = None) -> Dict:
        """Merge the catalogs"""
        if not target:
            return source

        merged = deepcopy(target)

        # Overwrite models that exist in both catalogs - merging catalog takes precedence
        for model in merged["nodes"]:
            if model in source["nodes"]:
                merged["nodes"][model] = source["nodes"][model]

        # Add models that exist in merging catalog but not in base catalog
        for model in source["nodes"]:
            if model not in merged["nodes"]:
                merged["nodes"][model] = source["nodes"][model]

        return merged

    def _trigger_job(self, job_id: int, body: Dict) -> Dict:
        """Trigger a job"""
        base_url = f"/api/v2/accounts/{self.account_id}/jobs/{job_id}/run"
        return self._dbt_cloud_api_request(
            base_url,
            http_method=HTTPMethod.POST,
            body=body,
        )

    # NOTE: this is currently unused and not tested, but did not want
    #       to remove it in case we end up using it soon. Should be cleaned
    #       up in a future PR.

    # def trigger_jobs_on_opendapi_ci_pass(
    #     self,
    #     github_pr_number: int,
    #     branch_name: str,
    # ) -> None:
    #     """Trigger the jobs on opendapi ci pass"""

    #     jobs = self._get_ci_jobs(
    #         self.account_id, self.project_id, OPENDAPI_JOB_SUFFIX_TRIGGER
    #     )
    #     # NOTE: for these PR jobs we want to set the commit status,
    #     #       so we need to pass in the PR number
    #     #       and do not use schema_override
    #     body = {
    #         "cause": "opendapi-metadata-analysis-passed",
    #         "github_pull_request_id": github_pr_number,
    #         "git_branch": branch_name,
    #     }
    #     # NOTE: not filtering for endswith to be a little more flexible
    #     for job in jobs:
    #         self._trigger_job(job["id"], body)

    def _trigger_opendapi_fast_docs_job(
        self,
        github_pr_number: Optional[int],
        branch_name: Optional[str],
        commit_type: CommitType,
    ) -> Dict:
        """Trigger the opendapi job"""
        # for now we only do this for PRs
        if github_pr_number is None or branch_name is None:
            raise RuntimeError("PR number or branch name not supplied for CI job")

        body = {
            "cause": "opendapi_ci_initiated",
            # We will explicitly generate docs in a command for modified models
            # this is so DBT does not try to generate docs for all models
            "generate_docs_override": False,
            # Modified/New models and their downstream models
            "steps_override": [
                # NOTE: We are excluding tests, snapshot, unit_tests, analysis, saved_query
                #       but they still come through in the manifest
                #       one build command is better than multiple to avoid parsing/compiling costs
                "dbt build --select state:modified+ --empty "
                "--exclude-resource-type test snapshot unit_test analysis",
                # NOTE: We will generate only for modified
                #       because we will merge with production catalog
                "dbt docs generate --select state:modified+",
            ],
            # NOTE: We do NOT want this to set a commit status.
            #       But, if we pass in the PR number and the commit sha the
            #       commit status gets set. Instead, if only pass in the git sha,
            #       no commit status is set, but then we want to ensure that
            #       the schema is still associated with the PR, and so we do this by
            #       setting the `schema_override` to the pattern that dbt cloud
            #       checks for when cleaning up PR presence.
            "git_branch": branch_name,
            "github_pull_request_id": github_pr_number,
            "schema_override": self.get_custom_schema(github_pr_number, commit_type),
        }
        triggered_run = self._trigger_job(self.ci_job_id, body)
        print_cli_output(f"Triggered run at: {self.build_run_html_url(triggered_run)}")
        return triggered_run

    def ensure_opendapi_job_initiated(
        self,
        github_pr_number: Optional[int],
        branch_name: Optional[str],
        commit_sha: str,
        commit_type: CommitType,
    ) -> Dict:
        """Ensure the opendapi job is initiated"""
        print_cli_output(
            f"Checking if there is an ongoing run for job {self.ci_job_id} for project "
            f"{self.project_id} and commit sha {commit_sha}."
        )
        run = self.get_latest_ci_run(
            match_git_sha=commit_sha,
            statuses={
                DBT_CLOUD_RUN_STATUSES["queued"],
                DBT_CLOUD_RUN_STATUSES["starting"],
                DBT_CLOUD_RUN_STATUSES["running"],
                DBT_CLOUD_RUN_STATUSES["success"],
            },
            job_id=self.ci_job_id,
        )
        if run:
            print_cli_output(
                f"Found an ongoing run for job {self.ci_job_id} for project "
                f"{self.project_id} and commit sha {commit_sha}. We will wait for it "
                "to complete."
            )
            print_cli_output(f"Run URL: {self.build_run_html_url(run)}")
            return run

        print_cli_output(
            f"No ongoing run found. We will trigger a new run for job {self.ci_job_id} "
            f"for project {self.project_id} and commit sha {commit_sha}."
        )
        print_cli_output("Triggering opendapi job")
        return self._trigger_opendapi_fast_docs_job(
            github_pr_number, branch_name, commit_type
        )

    @classmethod
    def get_account_id(
        cls,
        dbt_cloud_url: str,
        api_key: str,
    ) -> int:
        """Get the account id"""
        # must have at least one account if this does not raise RequestException
        accounts = cls.dbt_cloud_api_request(
            dbt_cloud_url,
            api_key,
            "/api/v2/accounts/",
        )
        if len(accounts) > 1:  # pragma: no cover
            cls._logger.error(  # pylint: disable=no-member
                "More than one account found in dbt Cloud - %s", dbt_cloud_url
            )

        return accounts[0]["id"]

    @classmethod
    def get_dbt_cloud_projects(
        cls: Type[DBTCloudProjectBaseType],
        dbt_cloud_url: str,
        api_key: str,
        filter_for_repo: Optional[str] = None,
        ensure_opendapi_job_exists: bool = True,
    ) -> Dict[str, DBTCloudProjectBaseType]:
        """Get the dbt cloud projects"""

        account_id = cls.get_account_id(dbt_cloud_url, api_key)

        dbt_cloud_projects = {}
        projects = cls.dbt_cloud_api_request(
            dbt_cloud_url,
            api_key,
            f"/api/v2/accounts/{account_id}/projects/",
        )

        for project in projects:
            repo_name = project["repository"]["full_name"]
            repo_subdirectory = project.get("dbt_project_subdirectory") or ""
            prod_docs_job_id = project.get("docs_job_id")

            if filter_for_repo is not None and filter_for_repo != repo_name:
                cls._log_text(
                    f"Skipping project {project['name']} because the repo it is "
                    f"associated with is {repo_name} does not match current repo "
                    f"{filter_for_repo}"
                )
                continue

            dbt_cp = cls(
                dbt_cloud_url=dbt_cloud_url,
                api_key=api_key,
                project_id=project["id"],
                account_id=account_id,
                repo_name=repo_name,
                project_name=project["name"],
                subdirectory=repo_subdirectory,
                prod_docs_job_id=prod_docs_job_id,
                ensure_opendapi_job_exists=ensure_opendapi_job_exists,
            )
            if dbt_cp.unique_name not in dbt_cloud_projects:
                dbt_cloud_projects[dbt_cp.unique_name] = dbt_cp
            else:  # pragma: no cover
                cls._logger.error(  # pylint: disable=no-member
                    "Duplicate project found for repository '%s' in dbt Cloud: %s",
                    dbt_cp.unique_name,
                    account_id,
                )
        return dbt_cloud_projects


class DBTCloudProject(DBTCloudProjectBase):
    """DBT Cloud project"""

    _logger: Logger = logger
    _log_text: Callable[[str], None] = print_cli_output


class DBTCloudMixin:
    """
    A mixin plugin used for adding dbt_cloud support to DBT DAPI validator.
    This plugin helps with downloading the dbt models from dbt cloud.
    """

    _dbt_commit_sha: Optional[str]
    _github_pr_number: Optional[int]
    _branch_name: Optional[str]
    _fast_fail: bool = False

    def _sync_dbt_cloud_artifacts(
        self,
        dbt_cps_with_projects: List[Tuple["DBTProject", DBTCloudProject]],
        commit_sha: str,
        fast_fail_runs_by_project: Optional[Dict[int, Dict]] = None,
    ) -> bool:
        """Sync the dbt projects from dbt cloud"""
        fast_fail_runs_by_project = fast_fail_runs_by_project or {}

        for opendapi_project_info, dbt_cp in dbt_cps_with_projects:

            # performance optimization
            if opendapi_project_info.has_cloud_artifacts:  # pragma: no cover
                continue

            # we do not check for the specifi job here, just in case another
            # job with docs generation happens to finish first
            success_run = dbt_cp.get_latest_ci_run(
                match_git_sha=commit_sha,
            )
            if not success_run:
                # if there is a run for us to check for fast fail, we do that
                if run := fast_fail_runs_by_project.get(dbt_cp.project_id):
                    ongoing_run = dbt_cp.get_latest_ci_run(
                        # we do not want to match the commit sha as we know the run ID
                        # besides dbt sets git sha only after the run is completed
                        # and we don't send that as part of the trigger
                        match_git_sha=None,
                        statuses={},
                        job_id=run["job"]["id"],
                        only_run_ids={run["id"]},
                    )
                    has_run_failed = ongoing_run and ongoing_run["status"] in {
                        DBT_CLOUD_RUN_STATUSES["error"],
                        DBT_CLOUD_RUN_STATUSES["cancelled"],
                    }
                    is_run_pending = ongoing_run and ongoing_run["status"] in {
                        DBT_CLOUD_RUN_STATUSES["queued"],
                        DBT_CLOUD_RUN_STATUSES["starting"],
                        DBT_CLOUD_RUN_STATUSES["running"],
                    }
                    # Because we trigger the job on the branch and not a SHA
                    # a race condition can happen where the job is triggered
                    # after a new commit was pushed to the same branch
                    # so we need to check for any run for the commit
                    # and if there is not one, we want to raise an error
                    is_run_missing = (
                        not ongoing_run or ongoing_run.get("git_sha") != commit_sha
                    ) and not is_run_pending

                    if has_run_failed or is_run_missing:
                        failure_message = (
                            (
                                f"The dbt Cloud job failed for project {dbt_cp.project_id} "
                                f"and commit {commit_sha} at run ID {ongoing_run['id']}."
                            )
                            if has_run_failed
                            else (
                                f"The dbt Cloud job did not run for project {dbt_cp.project_id}"
                                f" and commit {commit_sha}."
                            )
                        )
                        print_cli_output(failure_message)

                        failure_action = (
                            (
                                f"Check logs at {DBTCloudProject.build_run_html_url(ongoing_run)} "
                                "or the dbt cloud UI for more details and potential dbt errors to resolve."
                            )
                            if not is_run_missing
                            else (
                                "A new commit was likely added to this branch. If so, it is safe to ignore this error."
                            )
                        )

                        error_message = " ".join([failure_message, failure_action])

                        # NOTE: in the future we should update this to be a ClickException
                        #       that we do not count as an OpenDAPI failure
                        #       (filter it out server side),
                        #       since this is a problem with their PR/dbt cloud. But, for now,
                        #       we want to be alerted to this, and so we raise an error that
                        #       goes to sentry.

                        if self._fast_fail:
                            raise RuntimeError(highlight_message(error_message))

                        # if we are not fast failing, we want to check
                        # if there is a fallback run on the same SHA
                        # and if there is not, we want to raise an error and short circuit
                        fallback_run = dbt_cp.get_latest_ci_run(
                            match_git_sha=commit_sha,
                            statuses={
                                DBT_CLOUD_RUN_STATUSES["queued"],
                                DBT_CLOUD_RUN_STATUSES["starting"],
                                DBT_CLOUD_RUN_STATUSES["running"],
                                DBT_CLOUD_RUN_STATUSES["success"],
                            },
                        )
                        if not fallback_run:
                            error_message = " ".join(
                                [
                                    error_message,
                                    "No other fallback runs were found for this commit on dbt cloud.",
                                ]
                            )
                            raise RuntimeError(highlight_message(error_message))

                        print_cli_output(
                            "Waiting for the fallback run to complete: "
                            f"{DBTCloudProject.build_run_html_url(fallback_run)}"
                        )

                # did not fast fail, but there was no success_run, so
                # continue
                # NOTE: this is actually hit in tests, older python versions
                #       are just not counting it in coverage - 3.11 does
                continue  # pragma: no cover

            ci_manifest = dbt_cp.get_manifest_for_ci_run(success_run["id"])
            ci_catalog = dbt_cp.get_catalog_for_ci_run(success_run["id"])
            prod_catalog = dbt_cp.get_production_catalog()

            opendapi_project_info.cloud_manifest = ci_manifest
            opendapi_project_info.cloud_catalog = ci_catalog
            opendapi_project_info.cloud_production_catalog = prod_catalog

        return all(
            opendapi_project_info.has_cloud_artifacts
            for opendapi_project_info, _ in dbt_cps_with_projects
        )

    @staticmethod
    def _get_dbt_cloud_projects_with_projects(
        projects: List["DBTProject"],
    ) -> List[Tuple["DBTProject", DBTCloudProject]]:
        """
        Get the dbt cloud projects with their project

        NOTE: we do it in this clumsy list-of-tuples manner
              since projectinfo are not hashable, and while we can make them hashable
              on id or on hash((name, full_path, artifact_full_path)), we do not do that
              since it makes some assumptions about the opendapi config setup, and
              would therefore require additional validation... and this is simple enough
        """
        dbt_cps = DBTCloudProject.get_dbt_cloud_projects(
            dbt_cloud_url=os.environ["DAPI_DBT_CLOUD_URL"],
            api_key=os.environ["DAPI_DBT_CLOUD_API_TOKEN"],
            filter_for_repo=os.environ["GITHUB_REPOSITORY"],
        ).values()

        dbt_cps_with_projects = []
        for dbt_cp in dbt_cps:
            opendapi_project_infos = [
                opendapi_project_info
                for opendapi_project_info in projects
                if opendapi_project_info.full_path.endswith(dbt_cp.subdirectory)
            ]

            if not opendapi_project_infos:
                raise RuntimeError(
                    f"No opendapi project infos found for project {dbt_cp.project_id}"
                )

            if len(opendapi_project_infos) > 1:  # pragma: no cover
                raise RuntimeError(
                    f"Multiple opendapi project infos found for project {dbt_cp.project_id}"
                )

            dbt_cps_with_projects.append((opendapi_project_infos[0], dbt_cp))

        return dbt_cps_with_projects

    def sync_dbt_cloud_artifacts(self, projects: List["DBTProject"]) -> bool:
        """Sync the dbt projects from dbt cloud with a retry"""

        if not os.environ.get("DAPI_DBT_CLOUD_API_TOKEN") or not os.environ.get(
            "DAPI_DBT_CLOUD_URL"
        ):
            logger.info("DBT Cloud API token or URL not found")
            return False

        if not self._dbt_commit_sha or not os.environ.get("GITHUB_REPOSITORY"):
            logger.info("GITHUB_HEAD_SHA or GITHUB_REPOSITORY not found")
            return False

        dbt_cps_with_projects = self._get_dbt_cloud_projects_with_projects(projects)

        # we first check if there are already artifacts
        print_cli_output("Checking if artifacts exist")
        if self._sync_dbt_cloud_artifacts(dbt_cps_with_projects, self._dbt_commit_sha):
            print_cli_output("Found artifacts")
            return True

        # if there were no artifacts found,
        # we check if we need to trigger a new run, or if there are some already running
        print_cli_output(
            f"No artifacts found. Ensuring that there is a run for "
            f"{OPENDAPI_DBT_CLOUD_JOB_NAME} for projects "
            f"{', '.join([str(dbt_cp.project_id) for _, dbt_cp in dbt_cps_with_projects])}"
        )
        # NOTE: for now we are only doing head commit - fast follow with base
        runs_by_project = {
            dbt_cp.project_id: dbt_cp.ensure_opendapi_job_initiated(
                self._github_pr_number,
                self._branch_name,
                self._dbt_commit_sha,
                CommitType.HEAD,
            )
            for _, dbt_cp in dbt_cps_with_projects
        }

        print_cli_output("Done. Beginning to wait for artifacts.")

        # now that we have at least one run in the works,
        # we can keep retrying for a bit till we get the artifacts,
        # retrying for a bit till we get the artifacts
        # By default, we will retry every 30 seconds for 10 minutes
        retry_count = int(os.environ.get("DAPI_DBT_CLOUD_RETRY_COUNT") or 40)
        retry_count = 0 if retry_count < 0 else retry_count
        retry_wait_secs = int(os.environ.get("DAPI_DBT_CLOUD_RETRY_INTERVAL") or 30)
        total_wait_time = retry_count * retry_wait_secs

        while retry_count >= 0:
            print_cli_output("Attempting to sync dbt cloud artifacts")

            if self._sync_dbt_cloud_artifacts(
                dbt_cps_with_projects,
                self._dbt_commit_sha,
                fast_fail_runs_by_project=runs_by_project,
            ):
                return True

            print_cli_output("Couldn't find any artifacts")
            if retry_count > 0:
                print_cli_output(f"Retrying {retry_count} more time(s)")
                time.sleep(retry_wait_secs)

            retry_count -= 1

        error_message = (
            f"Waited for {total_wait_time} seconds. "
            "However, some of these following runs did not complete successfully. "
            "Rerun this workflow when all the runs eventually succeed.\n\n"
        )
        for project_id, run in runs_by_project.items():
            error_message += f"Project ID: {project_id}, Run URL: {DBTCloudProject.build_run_html_url(run)}\n"
        print_cli_output(highlight_message(error_message))
        return False
