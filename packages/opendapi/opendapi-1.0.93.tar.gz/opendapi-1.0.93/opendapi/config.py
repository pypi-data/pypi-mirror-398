"""Manage the opendapi.config.yaml object"""

from __future__ import annotations

import base64
import json
import os
import re
from typing import Dict, List, Optional

from jsonschema import validate as jsonschema_validate

from opendapi.defs import CONFIG_FILEPATH_FROM_ROOT_DIR, IntegrationMode, ORMIntegration
from opendapi.models import NameTransform, PlaybookConfig
from opendapi.utils import fetch_schema, make_snake_case, read_yaml_or_json


def _extract_source_sink(playbook: PlaybookConfig, table_name: str) -> Dict:
    """Extract the source or sink from the playbook"""
    namespace = playbook.namespace
    name_transform = playbook.name_transform
    identifier = f"{playbook.identifier_prefix or ''}{NameTransform.apply(name_transform, table_name)}"
    data = {"identifier": identifier}
    if namespace:
        data["namespace"] = namespace
    return {"urn": playbook.datastore_urn, "data": data}


def construct_dapi_source_sink_from_playbooks(
    playbooks: List[PlaybookConfig], table_name: str
) -> Dict:
    """Construct the source and sink from the playbook"""
    sources = []
    sinks = []
    for playbook in playbooks:
        if playbook.type == "add_source_datastore":
            sources.append(_extract_source_sink(playbook, table_name))
        if playbook.type == "add_sink_datastore":
            sinks.append(_extract_source_sink(playbook, table_name))
    return {"sources": sources, "sinks": sinks}


def construct_owner_team_urn_from_playbooks(
    playbooks: List[PlaybookConfig], table_name: str, table_path: str
) -> Optional[str]:
    """Construct the team URN from the playbook"""
    for playbook in playbooks:
        if playbook.type == "add_owner_team" and is_model_in_allowlist(
            table_name, table_path, playbook.model_allowlist
        ):
            return playbook.team_urn

    return None


def construct_project_full_path(root_dir: str, project_path: str) -> str:
    """Construct the full path to the project"""
    # we expect the project path to be relative to the root path anyway
    stripped_project_path = (
        project_path.lstrip("/").rstrip("/") if project_path else project_path
    )
    if not stripped_project_path:
        return root_dir

    return os.path.normpath(os.path.join(root_dir, stripped_project_path))


def get_project_path_from_full_path(root_dir: str, full_path: str) -> str:
    """Get the project path from the full path"""
    return os.path.relpath(full_path, root_dir)


def is_model_in_allowlist(
    model_name: str,
    abs_model_path: str | None,
    model_allowlist: List[str],
) -> bool:
    """Check if the model name is in the list of regex in model allowlist"""
    if not model_allowlist:
        return True

    model_path_allow = []
    model_name_allow = []
    model_path_deny = []
    model_name_deny = []

    def _match_regex(candidate: str, patterns: List[str]) -> bool:
        return any(
            re.compile(pattern, flags=re.IGNORECASE).match(candidate)
            for pattern in patterns
        )

    for itm in model_allowlist:
        is_deny = itm.startswith("!")
        pattern = itm[1:] if is_deny else itm

        if pattern.startswith("path:"):
            target_list = model_path_deny if is_deny else model_path_allow
            target_list.append(pattern.split("path:")[1])
        else:
            target_list = model_name_deny if is_deny else model_name_allow
            target_list.append(pattern)

    # First check if model matches any deny patterns - these take precedence
    if model_name and model_name_deny and _match_regex(model_name, model_name_deny):
        return False

    if (
        abs_model_path
        and model_path_deny
        and _match_regex(abs_model_path, model_path_deny)
    ):
        return False

    # If there are no allow patterns, everything not denied is allowed
    if not model_name_allow and not model_path_allow:
        return True

    # Otherwise, check if model matches any allow patterns
    match_model_name = (
        _match_regex(model_name, model_name_allow)
        if model_name and model_name_allow
        else False
    )
    match_model_path = (
        _match_regex(abs_model_path, model_path_allow)
        if abs_model_path and model_path_allow
        else False
    )

    return match_model_name or match_model_path


class OpenDAPIConfig:
    """Manage the opendapi.config.yaml object"""

    DEFAULT_RUNTIME = "DEFAULT"

    def __init__(
        self,
        root_dir: str,
        local_spec_path: Optional[str] = None,
        serialized_config: Optional[str] = None,
    ):
        self.root_dir = root_dir
        self.config = (
            self._load_config(serialized_config)
            if serialized_config
            else self._read_config()
        )
        self.local_spec_path = local_spec_path

    @staticmethod
    def ensure_schema_add_backfills(config: dict, ensure_schema: bool = True) -> dict:
        """Ensure the schema backfill runtimes are present"""
        if ensure_schema and "schema" not in config:
            raise ValueError("Invalid OpenDAPI config file: missing schema")

        if "repository" in config and "integration_mode" not in config["repository"]:
            integration_mode = os.environ.get("WOVEN_INTEGRATION_MODE")
            if not integration_mode:  # pragma: no cover
                raise ValueError(
                    "Invalid OpenDAPI config file: missing integration mode"
                )

            if integration_mode == "shadow":
                integration_mode = "observability"

            config["repository"]["integration_mode"] = integration_mode

        # NOTE: this is a HACK to allow configs that do not specify runtimes
        #       to still work with the new runtime structure
        if "runtimes" not in config["dapis"]:
            config["dapis"]["runtimes"] = {
                OpenDAPIConfig.DEFAULT_RUNTIME: {
                    "integrations": config["dapis"].pop("integrations")
                }
            }

        return config

    def _load_config(self, serialized_config: str) -> dict:
        """Load the config from the file"""
        return self.ensure_schema_add_backfills(
            json.loads(base64.b64decode(serialized_config))
        )

    def _read_config(self) -> dict:
        """Read the contents of the opendapi.config.yaml file"""
        config_file = self.config_full_path(self.root_dir)
        if os.path.exists(config_file):
            content = read_yaml_or_json(config_file)
            return self.ensure_schema_add_backfills(content)

        raise FileNotFoundError(f"OpenDAPI config file not found: {config_file}")

    @property
    def integration_mode(self) -> IntegrationMode:
        """Return the integration mode"""
        return IntegrationMode(self.config["repository"]["integration_mode"])

    @property
    def org_name(self) -> str:
        """Return the organization name"""
        return self.config["organization"]["name"]

    @property
    def org_name_snakecase(self) -> str:
        """Return the organization name in snake case"""
        return make_snake_case(self.org_name)

    @property
    def org_email_domain(self) -> str:
        """Return the organization email domain"""
        return self.config["organization"]["email_domain"]

    @staticmethod
    def config_full_path(root_dir: str) -> str:
        """Return the full path to the opendapi.config.yaml file"""
        return os.path.join(root_dir, CONFIG_FILEPATH_FROM_ROOT_DIR)

    @property
    def runtime_names(self) -> List[str]:
        """Return the list of runtime names"""
        return list(self.config["dapis"]["runtimes"].keys())

    def get_integration_types(self, runtime: str) -> List[ORMIntegration]:
        """Return the list of DAPI integrations"""

        integration_configs = self.config["dapis"]["runtimes"][runtime]["integrations"]
        integration_types = [
            ORMIntegration(integration["type"]) for integration in integration_configs
        ]
        return integration_types

    def has_integration(
        self,
        integration_type: ORMIntegration,
        runtime: str,
    ) -> bool:
        """Return True if the integration type is in the list of integrations"""
        return integration_type in self.get_integration_types(runtime)

    def get_integration_config(
        self, integration_type: ORMIntegration, runtime: str
    ) -> Dict:
        """Return the config for the integration type"""

        integration_configs = self.config["dapis"]["runtimes"][runtime]["integrations"]
        for integration in integration_configs:
            if integration["type"] == integration_type.value:
                return integration
        raise ValueError(
            f"Integration type not found in {CONFIG_FILEPATH_FROM_ROOT_DIR}: {integration_type}"
        )

    def get_mainline_branch(self) -> str:
        """Return the mainline branch"""
        return self.config["repository"]["mainline_branch"]

    def validate(self) -> None:
        """Return True if the config file is valid"""
        if self.local_spec_path is not None:
            schema_file = os.path.basename(self.config["schema"])
            schema_path = os.path.join(self.local_spec_path, schema_file)
            schema = read_yaml_or_json(schema_path)
        else:
            schema = fetch_schema(self.config["schema"])

        jsonschema_validate(self.config, schema)

    def assert_dapi_location_is_valid(
        self, loc: str, override: Optional[str] = None
    ) -> str:
        """
        Assert that the location for the file starts with the base
        """
        if not loc.startswith(override or self.root_dir):
            raise AssertionError(
                f"Dapi location, '{loc}', must be in the base dir, '{self.root_dir}', "
                "otherwise validator cannot find these files"
            )
        return loc

    def assert_single_runtime(self) -> str:
        """Assert that there is only one runtime, returns the runtime name"""
        runtime_names = self.runtime_names
        if len(runtime_names) != 1:
            raise RuntimeError(
                f"Expected exactly one runtime, found {len(runtime_names)}: {runtime_names}"
            )
        return runtime_names[0]

    def assert_runtime_exists(self, runtime: str) -> str:
        """Assert that the runtime exists, returns the runtime name"""
        if runtime not in self.runtime_names:
            raise RuntimeError(
                f"Runtime '{runtime}' not found in {CONFIG_FILEPATH_FROM_ROOT_DIR}. "
                f"The available runtimes are: {self.runtime_names}"
            )
        return runtime

    def get_serialized(self) -> dict:
        """Return the config for the file"""
        return base64.b64encode(json.dumps(self.config).encode()).decode()
