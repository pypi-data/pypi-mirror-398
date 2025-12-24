"""SqlAlchemy DAPI validator module"""

# pylint: disable=duplicate-code

import copy
import importlib.util
import os
import sys
import traceback
from dataclasses import dataclass
from functools import cached_property
from multiprocessing import Pipe, Process, connection
from typing import TYPE_CHECKING, Dict, List, Optional

from opendapi.adapters.file import find_files_with_suffix
from opendapi.config import (
    construct_dapi_source_sink_from_playbooks,
    construct_owner_team_urn_from_playbooks,
    construct_project_full_path,
    get_project_path_from_full_path,
)
from opendapi.logging import logger
from opendapi.models import ProjectConfig
from opendapi.validators.dapi.base.main import ORMIntegration
from opendapi.validators.dapi.base.runtime import RuntimeDapiValidator
from opendapi.validators.dapi.models import ProjectInfo

if TYPE_CHECKING:
    from sqlalchemy import MetaData, Table  # pragma: no cover

PROCESS_TIMEOUT = 120


@dataclass
class SqlAlchemyProjectInfo(ProjectInfo):
    """Data class for a sqlalchemy project information"""

    metadata_variable: Optional[str] = None

    def _sqlalchemy_column_type_to_dapi_datatype(self, column_type: str) -> str:
        """Convert the SQLAlchemy column type to DAPI data type"""
        try:
            return str(column_type).lower()
        except Exception:  # pylint: disable=broad-except  # pragma: no cover
            # likely compilation errors from old versions of sqlalchemy
            # e.g. str(JSON()) fails in sqlalchemy 1.3.19
            return getattr(
                column_type,
                "__visit_name__",
                column_type.__class__.__name__.lower(),
            ).lower()

    @property
    def service_name(self) -> str:
        """Get the service name"""
        return get_project_path_from_full_path(self.root_path, self.full_path).replace(
            "/", "."
        )

    def build_fields_for_table(self, table: "Table") -> List[Dict]:
        """Build the fields for the table"""
        fields = []
        for column in table.columns:
            fields.append(
                {
                    "name": str(column.name),
                    "data_type": self._sqlalchemy_column_type_to_dapi_datatype(
                        column.type
                    ),
                    "is_nullable": column.nullable,
                }
            )
        fields.sort(key=lambda x: x["name"])
        return fields

    def build_primary_key_for_table(self, table: "Table") -> List[str]:
        """Build the primary key for the table"""
        primary_key = []
        for column in table.columns:
            if column.primary_key:
                primary_key.append(str(column.name))
        return primary_key

    def _get_tables(self):
        """Get the tables for the project"""
        # Import the module
        sys.path.append(self.full_path)
        spec = importlib.util.spec_from_file_location(
            f"artifact_path_{self.artifact_full_path.replace('/', '__')}",
            self.artifact_full_path,
        )
        env_module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(env_module)
        except Exception as e:  # pylint: disable=broad-except
            # It's possible that some side-effect pieces are not runnable in the artifact path,
            # so we ignore the error
            # and continue hoping that the metadata has been loaded
            if not getattr(env_module, self.metadata_variable, None):
                raise e

        metadata: MetaData = getattr(env_module, self.metadata_variable)

        parsed_tables = []
        for table in metadata.sorted_tables:
            parsed_tables.append(
                {
                    "name": table.name,
                    "fullname": table.fullname,
                    "fields": self.build_fields_for_table(table),
                    "primary_key": self.build_primary_key_for_table(table),
                    "schema": table.schema,
                }
            )
        return parsed_tables

    def _tables(self, conn: connection.Connection):
        """Get the tables for the project"""
        # Import the module
        try:
            conn.send(self._get_tables())
        except Exception as e:
            # Cannot send the exception directly from the child, so we send the error message
            error_message = "".join(
                traceback.format_exception(type(e), e, e.__traceback__)
            )
            conn.send(error_message)
            raise e

    @cached_property
    def tables(self) -> List["Table"]:
        """Get the tables for the project"""
        # We import project levels modules in a separate process to avoid any side effects
        # that may occur when importing modules
        parent_conn, child_conn = Pipe(duplex=False)
        process = Process(target=self._tables, args=(child_conn,))
        process.start()
        process.join(PROCESS_TIMEOUT)

        if process.exitcode:
            if parent_conn.poll():
                error_message = parent_conn.recv()
                logger.info(error_message)
                raise ImportError(
                    f"Error importing {self.artifact_full_path}:{self.metadata_variable} "
                    f"\nMessage: {error_message}"
                )
            raise ImportError(  # pragma: no cover
                f"Error importing {self.artifact_full_path}:{self.metadata_variable} "
                "\nNo error message received"
            )

        # Receive the sorted tables from the child process
        sorted_tables = parent_conn.recv()
        return sorted_tables

    def filter_dapis(self, dapis: Dict[str, Dict]) -> Dict[str, Dict]:
        """Get the owned DAPIs"""
        return {
            filepath: dapi
            for filepath, dapi in dapis.items()
            if dapi.get("context", {}).get("service") == self.service_name
        }


class SqlAlchemyDapiValidator(RuntimeDapiValidator[SqlAlchemyProjectInfo]):
    """Validator class for DAPI files created for SQLAlchemy datasets"""

    INTEGRATION_NAME = ORMIntegration.SQLALCHEMY

    # App identifiers are comma separated values specified as the following:
    # "path/to/module.py:metadata"
    # "alembic/env.py:target_metadata
    # "path/to/app.py:metadata, path/to/sql_imports.py:sql_metadata"
    APP_IDENTIFIERS = "alembic/env.py:target_metadata"

    # Ignore the following file patterns when searching for schema files
    EXCLUDE_DIRS = []

    def build_datastores_for_table(
        self, project: SqlAlchemyProjectInfo, table_name: str
    ) -> Dict:
        """Build the datastores for the table"""
        return self.add_non_playbook_datastore_fields(
            construct_dapi_source_sink_from_playbooks(
                project.config.playbooks, table_name
            )
            if project.config.playbooks
            else {"sources": [], "sinks": []}
        )

    def build_urn_for_table(self, project: SqlAlchemyProjectInfo, table_name) -> str:
        """Build the urn for the table"""
        return (
            f"{project.org_name_snakecase}.{self.INTEGRATION_NAME.value}."
            f"{project.service_name}.{table_name}"
        )

    def get_project(self, project_config: ProjectConfig) -> SqlAlchemyProjectInfo:
        """Given an project override configuration, return the project config"""

        copy_project_config = copy.deepcopy(project_config)

        project_full_path = construct_project_full_path(
            self.root_dir, copy_project_config.project_path
        )

        if copy_project_config.artifact_path is None:
            raise ValueError("artifact_path is required in the configuration")

        artifact_path, metadata = copy_project_config.artifact_path.split(":")
        artifact_full_path = os.path.join(project_full_path, artifact_path)

        copy_project_config.artifact_path = artifact_path
        copy_project_config.include_models = (
            copy_project_config.include_models or self.integration_config.include_models
        )

        project = SqlAlchemyProjectInfo(
            org_name_snakecase=self.config.org_name_snakecase,
            root_path=self.root_dir,
            config=copy_project_config,
            full_path=project_full_path,
            artifact_full_path=artifact_full_path,
            metadata_variable=metadata,
        )

        return project

    def get_all_projects(self) -> List[SqlAlchemyProjectInfo]:
        """Get projects from all prisma schema files."""

        # App identifiers are comma separated values specified as the following:
        # "alembic/env.py:target_metadata
        # "path/to/app.py:metadata"
        # "path/to/sql_imports.py:sql_metadata"

        artifacts = [
            x.strip()
            for x in f"{self.integration_config.artifact_path or self.APP_IDENTIFIERS}".split(
                ","
            )
        ]
        projects = []

        for entry in artifacts:
            app, metadata = entry.split(":")
            file_pattern = f"/{app}"
            import_files = find_files_with_suffix(
                self.root_dir, [file_pattern], exclude_dirs=self.EXCLUDE_DIRS
            )

            for import_file in import_files:
                base_dir = import_file.replace(file_pattern, "")
                project_path = get_project_path_from_full_path(self.root_dir, base_dir)
                artifact_path = get_project_path_from_full_path(base_dir, import_file)
                artifact_path = f"{artifact_path}:{metadata}"

                override = ProjectConfig(
                    project_path=project_path,
                    artifact_path=artifact_path,
                    include_models=self.integration_config.include_models,
                )
                projects.append(self.get_project(override))

        return projects

    def _unskipped_validate_projects(self, projects: List[SqlAlchemyProjectInfo]):
        """Verify that all projects and their schema files exist"""
        for project in projects:
            if not os.path.exists(project.full_path):
                raise FileNotFoundError(
                    f"Project path {project.full_path} does not exist"
                )

            if project.artifact_full_path.endswith(".py") and not os.path.exists(
                project.artifact_full_path
            ):
                raise FileNotFoundError(
                    f"Artifact path {project.artifact_full_path} does not exist"
                )

            if not project.metadata_variable:
                raise ValueError(
                    f"artifact_path misconfiguration for {project.config.project_path}"
                )

    def _get_dapis_for_project(self, project: SqlAlchemyProjectInfo) -> Dict[str, Dict]:
        """Build the base template for autoupdate for a given project"""
        result = {}

        for table in project.tables:

            if not project.is_model_included(table["name"], project.full_path):
                continue

            # Note this includes the schema as well
            table_full_name = table["fullname"]

            result[project.construct_dapi_location(table_full_name)] = (
                self.add_default_non_generated_schema_portions(
                    {
                        "urn": self.build_urn_for_table(project, table_full_name),
                        "owner_team_urn": construct_owner_team_urn_from_playbooks(
                            project.config.playbooks,
                            table_full_name,
                            project.full_path,
                        ),
                        "datastores": self.build_datastores_for_table(
                            project, table_full_name
                        ),
                        "fields": table["fields"],
                        "primary_key": table["primary_key"],
                        "context": {
                            "integration": self.INTEGRATION_NAME.value,
                            "service": project.service_name,
                            "rel_model_path": os.path.relpath(
                                project.artifact_full_path,
                                os.path.dirname(
                                    project.construct_dapi_location(table_full_name)
                                ),
                            ),
                        },
                    }
                )
            )
        return result

    def _unskipped_get_base_generated_files(self) -> Dict[str, Dict]:
        """Build the base template for autoupdate"""
        projects = self.selected_projects()
        result = {}
        for project in projects:
            result.update(self._get_dapis_for_project(project))

        return result
