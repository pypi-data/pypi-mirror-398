"""DDL parser based DAPI validator module"""

import copy
import os
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import ClassVar, Dict, Generic, List, Type, TypeVar

from opendapi.adapters.file import find_files_with_suffix
from opendapi.config import (
    construct_dapi_source_sink_from_playbooks,
    construct_owner_team_urn_from_playbooks,
    construct_project_full_path,
    get_project_path_from_full_path,
)
from opendapi.defs import ORMIntegration, SqlDialect
from opendapi.models import ProjectConfig
from opendapi.validators.base import ValidationError
from opendapi.validators.dapi.base.runtime import (
    RuntimeDapiValidator,
)
from opendapi.validators.dapi.models import ProjectInfo
from opendapi.validators.dapi.parsers.ddl import Table, parse_ddl


@dataclass
class DdlBasedProjectInfo(ProjectInfo):
    """Data class for an ddl based project information"""

    # DDL parser based projects must have a dialect
    # This is sourced from the opendapi config.
    # On py3.9, kw_only is not supported and ProjectInfo has a kwarg already,
    # we use NotImplemented for dialect even though it's required
    dialect: SqlDialect = NotImplemented
    integration: ORMIntegration = NotImplemented

    AUDITING_TABLE_NAMES = []

    @abstractmethod
    def _get_ddl(self) -> str:
        """
        Get the DDL from the project.

        This must be run in the project directory
        """

    @property
    def project_name(self) -> str:
        """Get the name of the project."""
        # create a period delimited name from the project directory name
        proj_path = get_project_path_from_full_path(self.root_path, self.full_path)
        return proj_path.strip("/").replace("/", ".")

    def _get_table_urn(self, table: Table) -> str:
        """Get the urn for the table."""
        return f"{self.org_name_snakecase}.{self.integration.value}.{self.project_name}.{table.fq_name}"

    def _construct_datastores(self, table: Table) -> List[str]:
        """Construct the datastores for the table."""
        return RuntimeDapiValidator.add_non_playbook_datastore_fields(
            construct_dapi_source_sink_from_playbooks(
                self.config.playbooks, table.fq_name
            )
            if self.config.playbooks
            else {"sources": [], "sinks": []}
        )

    def _construct_owner_team_urn(self, table: Table) -> str:
        """Construct the owner team urn for the table."""
        return construct_owner_team_urn_from_playbooks(
            self.config.playbooks, table.fq_name, self.full_path
        )

    def get_tables(self) -> Dict[str, Dict]:
        """
        Get the tables for the project.
        This is a wrapper around the tables property for threading.
        """
        return self.tables

    @property
    def tables(self) -> Dict[str, Dict]:
        """
        Get the generated tables
        1. Runs the ddl parser CLI to get the current revision DDL
        2. Parses it to get the tables.
        """
        ddl = self._get_ddl()
        tables = parse_ddl(ddl, self.dialect)

        result = {}
        filtered_table_name_paths = self.filter_included_models(
            [(table.fq_name, self.artifact_full_path) for table in tables]
        )
        filtered_tables = [
            table
            for table in tables
            if (table.fq_name, self.artifact_full_path) in filtered_table_name_paths
            # We don't need to generate DAPIs for the auditing tables
            # it's an auditing table internal to the framework.
            and table.fq_name.lower() not in self.AUDITING_TABLE_NAMES
        ]
        for table in filtered_tables:
            dapi_location = self.construct_dapi_location(table.fq_name)
            result[dapi_location] = {
                "urn": self._get_table_urn(table),
                "owner_team_urn": self._construct_owner_team_urn(table),
                "datastores": self._construct_datastores(table),
                "fields": [
                    {
                        "name": column.name,
                        "data_type": column.type,
                        "is_nullable": column.is_nullable,
                        **(
                            {"enum_values": column.enum_values}
                            if column.enum_values
                            else {}
                        ),
                    }
                    for column in table.columns
                ],
                "primary_key": (table.primary_key.columns if table.primary_key else []),
                "context": {
                    "integration": self.integration.value,
                    "service": self.project_name,
                    "rel_model_path": os.path.relpath(
                        self.artifact_full_path,
                        os.path.dirname(dapi_location),
                    ),
                },
            }
        return result


DdlBasedProjectInfoType = TypeVar("DdlBasedProjectInfoType", bound=DdlBasedProjectInfo)


class DdlBasedDapiValidator(
    RuntimeDapiValidator[DdlBasedProjectInfoType], Generic[DdlBasedProjectInfoType]
):
    """
    Validator class for DAPI files created for DDL based datasets
    """

    INTEGRATION_NAME: ORMIntegration = NotImplemented
    DEFAULT_ARTIFACT_PATH: str = NotImplemented
    EXCLUDE_DIRS_FOR_AUTODISCOVERY = []
    PROJECT_INFO_TYPE: ClassVar[Type[DdlBasedProjectInfoType]]

    def get_all_projects(self) -> List[DdlBasedProjectInfo]:
        """Get all projects from the artifact files."""

        artifact_path = (
            self.integration_config.artifact_path or self.DEFAULT_ARTIFACT_PATH
        )
        artifact_files = find_files_with_suffix(
            self.root_dir,
            [f"/{artifact_path}"],
            exclude_dirs=self.EXCLUDE_DIRS_FOR_AUTODISCOVERY,
        )

        projects = []
        for artifact_file in artifact_files:
            base_dir = artifact_file.replace(artifact_path, "")
            project_path = get_project_path_from_full_path(self.root_dir, base_dir)
            artifact_path = get_project_path_from_full_path(base_dir, artifact_file)

            override = ProjectConfig(
                project_path=project_path,
                artifact_path=artifact_path,
                dialect=self.integration_config.dialect,
                include_models=self.integration_config.include_models,
            )

            projects.append(self.get_project(override))

        return projects

    def get_project(self, project_config: ProjectConfig) -> DdlBasedProjectInfo:
        """Get the project for the artifact file."""
        copy_project_config = copy.deepcopy(project_config)
        project_full_path = construct_project_full_path(
            self.root_dir, copy_project_config.project_path
        )

        copy_project_config.artifact_path = (
            copy_project_config.artifact_path
            or self.integration_config.artifact_path
            or self.DEFAULT_ARTIFACT_PATH
        )
        copy_project_config.include_models = (
            copy_project_config.include_models or self.integration_config.include_models
        )

        try:
            dialect = SqlDialect(
                copy_project_config.dialect or self.integration_config.dialect
            )
        except ValueError as e:
            raise ValueError(
                f"SQL dialect not found for project {project_full_path}. "
                "Please specify the dialect in the project config."
            ) from e

        return self.PROJECT_INFO_TYPE(
            org_name_snakecase=self.config.org_name_snakecase,
            root_path=self.root_dir,
            config=copy_project_config,
            dialect=dialect,
            full_path=project_full_path,
            artifact_full_path=construct_project_full_path(
                project_full_path, copy_project_config.artifact_path
            ),
        )

    def _unskipped_validate_projects(self, projects: List[DdlBasedProjectInfo]):
        """Validate the projects."""
        errors = []
        for project in projects:
            # unlikely to reach here as the dialect is validated in the constructor
            # we will keep here just in case
            if (
                not project.dialect or project.dialect not in SqlDialect
            ):  # pragma: no cover
                errors.append(
                    f"SQL dialect not found for project {project.full_path}. "
                    "Please specify the dialect in the project config."
                )
            if not os.path.exists(project.artifact_full_path):
                errors.append(
                    f"{self.DEFAULT_ARTIFACT_PATH} file {project.artifact_full_path} not found "
                    f"for project {project.full_path}"
                )
        if errors:
            raise ValidationError("\n".join(errors))

    def _unskipped_get_base_generated_files(self) -> Dict[str, Dict]:
        """Get the base generated files."""
        result = {}
        # Run parallel jobs to get the tables
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(project.get_tables)
                for project in self.selected_projects()
            ]
            for future in as_completed(futures):
                tables: Dict[str, Dict] = future.result()
                for location, table_dict in tables.items():
                    result[location] = self.add_default_non_generated_schema_portions(
                        table_dict
                    )

        return result
