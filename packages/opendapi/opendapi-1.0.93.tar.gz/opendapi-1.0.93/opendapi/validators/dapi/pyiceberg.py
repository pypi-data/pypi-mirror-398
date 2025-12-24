"""Validators that use PyIceberg Schema syntax for Iceberg tables"""

import copy
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Union

from opendapi.adapters.file import find_files_with_suffix
from opendapi.config import (
    construct_dapi_source_sink_from_playbooks,
    construct_owner_team_urn_from_playbooks,
    construct_project_full_path,
    get_project_path_from_full_path,
)
from opendapi.models import ProjectConfig
from opendapi.utils import read_yaml_or_json
from opendapi.validators.dapi.base.main import DapiValidator, ORMIntegration
from opendapi.validators.dapi.models import ProjectInfo
from opendapi.validators.defs import IntegrationType


@dataclass
class PyIcebergProjectInfo(ProjectInfo):
    """Project info for PyIceberg based projects"""

    # Considered using pyiceberg library to parse the schema,
    # but it's just not very useful beyond validating the data types.
    # why take a dependency just for that? But, easy to cutover if needed.

    def _fmt_field_type(self, field_type: str) -> str:
        """Format the field type"""
        wo_type = field_type.rsplit("Type", 1)[0].lower()
        # Supports both simple types and pyiceberg types (e.g. IntegerType)
        return {
            "integer": "int",
            "timestampnano": "timestamp_ns",
            "timestamptznano": "timestamptz_ns",
        }.get(wo_type, wo_type)

    def _parse_field_type(self, field_type: Union[str, Dict]) -> str:
        """Parse the field type"""
        if isinstance(field_type, str):
            return self._fmt_field_type(field_type)
        root_typ = self._fmt_field_type(list(field_type.keys())[0])
        field_config = list(field_type.values())[0]

        if root_typ == "map":
            key_typ = self._parse_field_type(field_config["key_type"])
            value_typ = self._parse_field_type(field_config["value_type"])
            return f"{root_typ}<{key_typ}, {value_typ}>"
        if root_typ == "struct":
            # fields can be a list or nested under a 'fields' key
            nested_fields = (
                field_config["fields"]
                if isinstance(field_config, dict)
                else field_config
            )
            nested_field_types = [
                self._parse_field_type(
                    nested_field["field_type"]
                    if "field_type" in nested_field
                    else nested_field["type"]
                )
                for nested_field in nested_fields
            ]
            return f"{root_typ}<{', '.join(nested_field_types)}>"
        if root_typ == "list":
            return f"{root_typ}<{self._parse_field_type(field_config['element_type'])}>"

        return root_typ

    def table_name_from_artifact_path(self, artifact_path: str) -> str:
        """Get the table name from the artifact path"""
        return os.path.splitext(os.path.basename(artifact_path))[0]

    @property
    def project_name(self) -> str:
        """Get the project name"""
        project_path = get_project_path_from_full_path(self.root_path, self.full_path)
        return project_path.strip(os.sep).replace(os.sep, ".")

    def construct_table_urn(self, artifact_path: str) -> str:
        """Construct the urn for the table"""
        table_name = self.table_name_from_artifact_path(artifact_path)
        return f"{self.org_name_snakecase}.pyiceberg.{self.project_name}.{table_name}"

    def construct_datastores(self, table_name: str) -> List[str]:
        """Construct the datastores for the table"""
        return DapiValidator.add_non_playbook_datastore_fields(
            construct_dapi_source_sink_from_playbooks(self.config.playbooks, table_name)
            if self.config.playbooks
            else {"sources": [], "sinks": []}
        )

    def construct_owner_team_urn(self, table_name: str) -> str:
        """Construct the owner team urn for the table"""
        return construct_owner_team_urn_from_playbooks(
            self.config.playbooks, table_name, self.full_path
        )

    def get_tables(self) -> Dict[str, Dict]:
        """Get the tables for the project by location."""
        results = {}
        for artifact_full_path in self.artifact_full_path.split(","):
            table_name = self.table_name_from_artifact_path(artifact_full_path)

            if not table_name or not self.filter_included_models(
                [(table_name, artifact_full_path)]
            ):
                continue

            yml_content = read_yaml_or_json(artifact_full_path)
            try:
                _ = yml_content["schema"]["fields"][0]["field_type"]
                _ = yml_content["schema"]["fields"][0]["name"]
            except (KeyError, IndexError):
                # This is not a valid PyIceberg schema, we will skip it
                continue

            dapi_cols_by_name = {}
            for col_dict in yml_content["schema"]["fields"]:
                field_id = (
                    col_dict["field_id"] if "field_id" in col_dict else col_dict["id"]
                )
                field_type = (
                    col_dict["field_type"]
                    if "field_type" in col_dict
                    else col_dict["type"]
                )
                name = col_dict["name"]
                required = col_dict.get("required", True)
                dapi_cols_by_name[col_dict["name"]] = {
                    "field_id": field_id,
                    "name": name,
                    "data_type": self._parse_field_type(field_type),
                    "is_nullable": not required,
                }

            identifier_field_ids = yml_content["schema"].get("identifier_field_ids", [])

            field_id_to_name = {
                col_dict["field_id"]: name
                for name, col_dict in dapi_cols_by_name.items()
                if col_dict["field_id"] is not None
            }

            primary_keys = [
                field_id_to_name[field_id]
                for field_id in identifier_field_ids
                if field_id in field_id_to_name
            ]

            dapi_location = self.construct_dapi_location(table_name)

            results[dapi_location] = {
                "urn": self.construct_table_urn(table_name),
                "owner_team_urn": self.construct_owner_team_urn(table_name),
                "datastores": self.construct_datastores(table_name),
                "fields": [
                    {
                        "name": col_name,
                        "data_type": col_dict["data_type"],
                        "is_nullable": col_dict["is_nullable"],
                    }
                    for col_name, col_dict in dapi_cols_by_name.items()
                ],
                "primary_key": primary_keys,
                "context": {
                    "integration": "pyiceberg",
                    "service": self.project_name,
                    "rel_model_path": os.path.relpath(
                        artifact_full_path, os.path.dirname(dapi_location)
                    ),
                },
            }

        return results


class PyIcebergDapiValidator(DapiValidator):
    """Validator for PyIceberg Schema syntax for Iceberg tables"""

    INTEGRATION_NAME = ORMIntegration.PYICEBERG
    INTEGRATION_TYPE = IntegrationType.STATIC

    DEFAULT_ARTIFACT_PATH: str = ".yml"
    EXCLUDE_DIRS_FOR_AUTODISCOVERY = []

    def get_all_projects(self) -> List[PyIcebergProjectInfo]:
        """Get all projects from the artifact files."""
        search_artifact_path = (
            self.integration_config.artifact_path or self.DEFAULT_ARTIFACT_PATH
        )
        anchor_files = find_files_with_suffix(
            self.root_dir,
            [*search_artifact_path.split(",")],
            exclude_dirs=self.EXCLUDE_DIRS_FOR_AUTODISCOVERY,
        )
        # KBTODO: will come back to better support the artifact path being a list
        anchor_files_by_project_path = defaultdict(list)
        for anchor_file in anchor_files:
            anchor_dir = os.path.dirname(anchor_file)
            project_path = get_project_path_from_full_path(self.root_dir, anchor_dir)
            artifact_path = os.path.basename(anchor_file)
            anchor_files_by_project_path[project_path].append(artifact_path)

        project_configs = [
            ProjectConfig(
                project_path=project_path,
                artifact_path=",".join(artifact_paths),
                include_models=self.integration_config.include_models,
            )
            for project_path, artifact_paths in anchor_files_by_project_path.items()
        ]
        projects = [self.get_project(config) for config in project_configs]
        return projects

    def get_project(self, project_config: ProjectConfig) -> PyIcebergProjectInfo:
        """Get the project for the artifact file."""
        copy_project_config = copy.deepcopy(project_config)
        project_full_path = construct_project_full_path(
            self.root_dir, copy_project_config.project_path
        )

        # It's possible that the artifact path may be comma-separated list of paths
        # KBTODO: better support artifact paths being a list
        search_artifact_path = (
            copy_project_config.artifact_path
            or self.integration_config.artifact_path
            or self.DEFAULT_ARTIFACT_PATH
        )
        anchor_files = find_files_with_suffix(
            project_full_path,
            [*search_artifact_path.split(",")],
            exclude_dirs=self.EXCLUDE_DIRS_FOR_AUTODISCOVERY,
        )
        copy_project_config.artifact_path = ",".join(
            [
                get_project_path_from_full_path(project_full_path, anchor_file)
                for anchor_file in anchor_files
            ]
        )
        artifact_full_paths = [
            os.path.join(project_full_path, anchor_file) for anchor_file in anchor_files
        ]

        copy_project_config.include_models = (
            copy_project_config.include_models or self.integration_config.include_models
        )
        return PyIcebergProjectInfo(
            org_name_snakecase=self.config.org_name_snakecase,
            root_path=self.root_dir,
            config=copy_project_config,
            full_path=project_full_path,
            artifact_full_path=",".join(artifact_full_paths),
        )

    def validate_projects(self, projects: List[PyIcebergProjectInfo]):
        """Validate the projects."""
        self.assert_artifact_files_exist(projects)

    def _get_base_generated_files(self) -> Dict[str, Dict]:
        """Get the base generated files."""
        result = {}
        for project in self.selected_projects():
            for location, table_dict in project.get_tables().items():
                result[location] = self.add_default_non_generated_schema_portions(
                    table_dict
                )
        return result
