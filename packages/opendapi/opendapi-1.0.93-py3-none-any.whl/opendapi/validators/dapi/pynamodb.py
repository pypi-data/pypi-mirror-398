"""PynamoDB DAPI validator module"""

import copy
import importlib
import inspect
import os
import sys
from dataclasses import dataclass
from functools import cached_property
from multiprocessing import Pipe, Process, connection
from typing import TYPE_CHECKING, Dict, List

from opendapi.adapters.file import find_subclasses_in_directory
from opendapi.config import (
    construct_dapi_source_sink_from_playbooks,
    construct_owner_team_urn_from_playbooks,
    construct_project_full_path,
)
from opendapi.logging import logger
from opendapi.models import ProjectConfig
from opendapi.validators.dapi.base.main import ORMIntegration
from opendapi.validators.dapi.base.runtime import RuntimeDapiValidator
from opendapi.validators.dapi.models import ProjectInfo

if TYPE_CHECKING:
    from pynamodb.models import Model  # pragma: no cover


PROCESS_TIMEOUT = 120


@dataclass
class PynamodbProjectInfo(ProjectInfo):
    """Data class for a sqlalchemy project information"""

    def _dynamo_type_to_dapi_datatype(self, dynamo_type: str) -> str:
        """Convert the DynamoDB type to DAPI data type"""
        dynamo_to_dapi = {
            "S": "string",
            "N": "number",
            "B": "binary",
            "BOOL": "boolean",
            "SS": "string_set",
            "NS": "number_set",
            "BS": "binary_set",
            "L": "array",
            "M": "object",
            "NULL": "null",
        }
        return dynamo_to_dapi.get(dynamo_type) or dynamo_type

    def build_fields_for_table(self, table: "Model") -> List[Dict]:
        """Build the fields for the table"""
        attrs = table.get_attributes()
        fields = []
        for _, attribute in attrs.items():
            fields.append(
                {
                    "name": attribute.attr_name,
                    "data_type": self._dynamo_type_to_dapi_datatype(
                        attribute.attr_type
                    ),
                    "is_nullable": attribute.null,
                }
            )
        fields.sort(key=lambda x: x["name"])
        return fields

    def build_primary_key_for_table(self, table: "Model") -> List[str]:
        """Build the primary key for the table"""
        attrs = table.get_attributes()
        hash_key, range_key = None, None
        for _, attribute in attrs.items():
            if attribute.is_hash_key:
                hash_key = attribute.attr_name
            if attribute.is_range_key:
                range_key = attribute.attr_name
        primary_key = [hash_key] if hash_key else []
        if range_key:
            primary_key.append(range_key)
        return primary_key

    def _get_tables(self):
        """Get the tables for the project"""
        # Import the module
        models = []
        base_classes = []
        sys.path.append(self.full_path)

        for import_string in self.config.artifact_path.split(","):
            import_string = import_string.strip()

            if ":" in import_string:
                module_name, class_name = import_string.split(":")
            else:
                module_name = import_string
                class_name = None

            module = importlib.import_module(module_name)

            if class_name:
                base_classes.append(getattr(module, class_name))

        # Now that all the modules are imported, we can get the tables by getting the
        # subclasses of the model
        for base_class in base_classes:
            new_models = find_subclasses_in_directory(
                self.full_path,
                base_class,
                exclude_dirs=["tests", "node_modules", ".venv", ".git"],
            )
            models.extend(new_models)

        parsed_models = [
            {
                "table_name": model.Meta.table_name,
                "fields": self.build_fields_for_table(model),
                "primary_key": self.build_primary_key_for_table(model),
                "service": model.__module__,
                "source_file": inspect.getfile(model),
            }
            for model in models
            if hasattr(model, "Meta")
        ]

        return parsed_models

    def _tables(self, conn: connection.Connection):
        """Get the tables for the project"""
        try:
            conn.send(self._get_tables())
        except Exception:
            logger.error(
                "Error generating tables info under %s in %s",
                self.config.artifact_path,
                self.full_path,
            )
            raise

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
            raise ImportError(
                f"Error generating tables: {self.config.artifact_path} in {self.full_path}"
            )

        # Receive the tables from the child process
        tables = parent_conn.recv()
        return tables


class PynamodbDapiValidator(RuntimeDapiValidator[PynamodbProjectInfo]):
    """
    Validator class for DAPI files created for Pynamo datasets
    """

    INTEGRATION_NAME = ORMIntegration.PYNAMODB

    # App identifiers are comma separated values specified as the following:
    # module.name:BaseModel,module.to.import1,module.to.import2,...
    # module.name:BaseModel
    # pynamodb.models:Model
    APP_IDENTIFIERS = "pynamodb.models:Model"

    def selected_projects(self, validate: bool = True) -> List[PynamodbProjectInfo]:
        """Get the selected projects"""
        if self.integration_config.include_all:
            raise ValueError("include_all:true is not supported for PynamoDB")
        return super().selected_projects()

    def get_project(self, project_config: ProjectConfig) -> PynamodbProjectInfo:
        """Given a project config, return ProjectInfo object"""

        copy_project_config = copy.deepcopy(project_config)

        project_full_path = construct_project_full_path(
            self.root_dir, copy_project_config.project_path
        )

        copy_project_config.artifact_path = (
            copy_project_config.artifact_path or self.APP_IDENTIFIERS
        )

        copy_project_config.include_models = (
            copy_project_config.include_models or self.integration_config.include_models
        )

        project = PynamodbProjectInfo(
            org_name_snakecase=self.config.org_name_snakecase,
            root_path=self.root_dir,
            config=copy_project_config,
            full_path=project_full_path,
            artifact_full_path=None,
        )

        return project

    def get_all_projects(self) -> List[PynamodbProjectInfo]:
        """Get projects from all prisma schema files."""
        raise RuntimeError("get_all_projects is not supported for PynamoDB")

    def _unskipped_validate_projects(self, projects: List[PynamodbProjectInfo]):
        """Verify that all projects and their schema files exist"""

    def build_datastores_for_table(
        self, project: PynamodbProjectInfo, table_name: str
    ) -> Dict:
        """Build the datastores for the table"""
        return self.add_non_playbook_datastore_fields(
            construct_dapi_source_sink_from_playbooks(
                project.config.playbooks, table_name
            )
            if project.config.playbooks
            else {"sources": [], "sinks": []}
        )

    def build_urn_for_table(self, project: PynamodbProjectInfo, table: Dict) -> str:
        """Build the urn for the table"""
        table_name = table["table_name"]
        service = table["service"].split(".")[0]

        project_path = project.config.project_path
        project_path = project_path.replace("/", ".")
        project_path = (
            service if project.full_path == project.root_path else project_path
        )

        return f"{project.org_name_snakecase}.{self.INTEGRATION_NAME.value}.{project_path}.{table_name}"

    def _reconcile_polymorphism(self, dapi_for_model: List[Dict]) -> List[Dict]:
        """Reconcile polymorphism in the DAPIs"""
        dapi_by_location = {}
        # Sort the dapi_for_model by table to have a consistent ordering of models
        # This prevents unnecessary diffs in the DAPI files on each run
        dapi_for_model = sorted(dapi_for_model, key=lambda x: x["table"]["source_file"])

        for value in dapi_for_model:
            location = value["location"]
            if location in dapi_by_location:
                # Union the fields across all polymorphic models
                # since they all correspond to the same underlying table
                existing_fields = dapi_by_location[location]["fields"]
                new_fields = value["dapi"]["fields"]
                for field in new_fields:
                    for existing_field in existing_fields:
                        if field["name"] == existing_field["name"]:
                            break
                    else:
                        existing_fields.append(field)
            else:
                dapi_by_location[location] = value["dapi"]

        for value in dapi_for_model:
            value["dapi"] = dapi_by_location[value["location"]]

        return dapi_for_model

    def _get_dapis_for_project(self, project: PynamodbProjectInfo) -> Dict[str, Dict]:
        """Get the DAPIs for the project"""
        dapi_for_model = []

        for table in project.tables:
            table_name = table["table_name"]

            if not project.is_model_included(table_name, project.full_path):
                continue

            entry = {
                "table": table,
                "location": project.construct_dapi_location(table_name),
                "dapi": self.add_default_non_generated_schema_portions(
                    {
                        "urn": self.build_urn_for_table(project, table),
                        "owner_team_urn": construct_owner_team_urn_from_playbooks(
                            project.config.playbooks, table_name, project.full_path
                        ),
                        "datastores": self.build_datastores_for_table(
                            project, table_name
                        ),
                        "primary_key": table["primary_key"],
                        "fields": table["fields"],
                        "context": {
                            "service": table["service"],
                            "integration": self.INTEGRATION_NAME.value,
                            "rel_model_path": os.path.relpath(
                                table["source_file"],
                                os.path.dirname(
                                    project.construct_dapi_location(table_name)
                                ),
                            ),
                        },
                    }
                ),
            }
            dapi_for_model.append(entry)

        result = {}
        for value in self._reconcile_polymorphism(dapi_for_model):
            result[value["location"]] = value["dapi"]

        return result

    def _unskipped_get_base_generated_files(self) -> Dict[str, Dict]:
        """Build the base template for autoupdate"""
        result = {}

        for project in self.selected_projects():
            result.update(self._get_dapis_for_project(project))

        return result
