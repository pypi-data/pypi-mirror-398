# pylint: disable=too-many-instance-attributes
"""DAPI validator module"""

import copy
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from typing import Dict, List, Optional, Tuple

from opendapi.adapters.file import find_files_with_suffix
from opendapi.config import (
    construct_dapi_source_sink_from_playbooks,
    construct_owner_team_urn_from_playbooks,
    construct_project_full_path,
    get_project_path_from_full_path,
)
from opendapi.logging import logger
from opendapi.models import ProjectConfig
from opendapi.utils import read_yaml_or_json
from opendapi.validators.dapi.base.main import DapiValidator, ORMIntegration
from opendapi.validators.dapi.mixins.dbt_cloud import DBTCloudMixin, DBTCloudProject
from opendapi.validators.dapi.models import ProjectInfo
from opendapi.validators.defs import IntegrationType
from opendapi.weakref import weak_lru_cache

DBT_CONFIG_YML = "dbt_project.yml"
DBT_ARTIFACTS_DIR = "target"
DBT_MANIFEST_JSON = "manifest.json"
DBT_CATALOG_JSON = "catalog.json"


class ColumnTestType(Enum):
    """Column test type"""

    UNIQUE = "unique"
    NOT_NULL = "not_null"


class ConstraintType(Enum):
    """Constraint type"""

    PRIMARY_KEY = "primary_key"
    NOT_NULL = "not_null"


@dataclass
class DBTProjectInfo(ProjectInfo):
    """DBT project"""

    name: Optional[str] = None
    dbt_config: Dict = field(default_factory=dict)
    cloud_manifest: Optional[Dict] = None
    cloud_catalog: Optional[Dict] = None
    cloud_production_catalog: Optional[Dict] = None

    @property
    def _catalog_path(self) -> str:
        """Get the catalog path"""
        return os.path.join(self.artifact_full_path, DBT_CATALOG_JSON)

    @property
    def _manifest_path(self) -> str:
        """Get the manifest path"""
        return os.path.join(self.artifact_full_path, DBT_MANIFEST_JSON)

    @property
    def _production_catalog_path(self) -> str:
        """Create the production catalog path"""
        return os.path.join(
            os.path.dirname(self._catalog_path),
            "prod",
            os.path.basename(self._catalog_path),
        )

    @cached_property
    def manifest(self) -> Dict:
        """Get the fallback manifest"""
        return self.cloud_manifest or read_yaml_or_json(self._manifest_path)

    @cached_property
    def raw_catalog(self) -> Dict:
        """Get the fallback catalog"""
        return self.cloud_catalog or read_yaml_or_json(self._catalog_path)

    @cached_property
    def production_catalog(self) -> Optional[Dict]:
        """Get the production catalog"""
        try:
            return self.cloud_production_catalog or read_yaml_or_json(
                self._production_catalog_path
            )
        except FileNotFoundError:
            return None

    @cached_property
    def catalog(self) -> Dict:
        """Get the merged catalog"""
        return DBTCloudProject.merge_catalogs(self.raw_catalog, self.production_catalog)

    @property
    def has_cloud_artifacts(self) -> bool:
        """Check if the project has artifacts"""
        return self.cloud_manifest and self.cloud_catalog


@dataclass
class DBTColumn:
    """DBT column"""

    name: str
    catalog_info: Dict
    manifest_info: Dict
    tests_from_manifest: List[str]

    @property
    def data_type(self) -> str:
        """Get the data type"""
        return self.catalog_info["type"].lower()

    @property
    def manifest_description(self) -> str:
        """Get the description from the manifest"""
        return self.manifest_info.get("description")

    @property
    def has_primary_key_constraint(self) -> bool:
        """Check if the column has a primary key constraint"""
        if self.manifest_info.get("constraints"):
            for contract in self.manifest_info["constraints"]:
                if contract.get("type") == ConstraintType.PRIMARY_KEY.value:
                    return True
        if ColumnTestType.UNIQUE.value in self.tests_from_manifest:
            return True
        return False

    @property
    def manifest_is_nullable(self) -> bool:
        """Check if the column is nullable"""
        if self.manifest_info.get("constraints"):
            for contract in self.manifest_info["constraints"]:
                if contract.get("type") == ConstraintType.NOT_NULL.value:
                    return False
        if ColumnTestType.NOT_NULL.value in self.tests_from_manifest:
            return False
        return True

    def for_dapi(self) -> Dict:
        """Get the column for DAPI"""
        return {
            "name": self.name,
            "data_type": self.data_type,
            "description": self.manifest_description or None,
            "is_nullable": self.manifest_is_nullable,
        }


@dataclass
class DBTModel:
    """DBT model"""

    name: str
    unique_id: str
    project: DBTProjectInfo
    is_allowlisted: bool = True

    def _property_from_manifest(self, property_name: str) -> str:
        """Get a property from the manifest"""
        return self.project.manifest["nodes"][self.unique_id][property_name]

    def _property_from_catalog(self, property_name: str) -> str:
        """Get a property from the catalog"""
        return self.project.catalog["nodes"][self.unique_id][property_name]

    def get_column_tests_from_manifest(self) -> Dict[str, List[str]]:
        """Get the tests from the manifest"""
        tests_by_column_names = {}
        for node in self.project.manifest["nodes"].values():
            model_unique_id = node.get("attached_node")
            if (
                node.get("resource_type") == "test"
                and model_unique_id == self.unique_id
            ):
                test_name = node.get("test_metadata", {}).get("name")
                if test_name:
                    column_name = node.get("column_name")
                    tests_by_column_names.setdefault(column_name, []).append(test_name)
        return tests_by_column_names

    @property
    def schema(self) -> str:
        """Get the schema from the manifest"""
        return self._property_from_manifest("schema")

    @property
    def model_path(self) -> str:
        """Get the model path"""
        return f"{self.project.full_path}/{self._property_from_manifest('original_file_path')}"

    @property
    def doc_path(self) -> Optional[str]:
        """Get the doc path"""
        patch_path = self._property_from_manifest("patch_path")
        if patch_path:
            return f"{self.project.full_path}/{patch_path.split('://')[1]}"
        return None

    @property
    def manifest_table_description(self) -> str:
        """Get the table description from the manifest"""
        return self._property_from_manifest("description")

    @staticmethod
    def extract_columns_from_artifacts(
        manifest_columns: Dict,
        catalog_columns: Dict,
        column_tests: Dict[str, List[str]],
    ) -> List[DBTColumn]:
        """Extract column info from manifest and catalog columns"""
        columns = []
        for column_name, catalog_info in catalog_columns.items():
            manifest_info = manifest_columns.get(
                column_name.lower(),
                manifest_columns.get(column_name, {}),
            )
            columns.append(
                DBTColumn(
                    name=column_name.lower(),
                    catalog_info=catalog_info,
                    manifest_info=manifest_info,
                    tests_from_manifest=column_tests.get(column_name.lower(), []),
                )
            )
        return columns

    @property
    def columns(self) -> List[DBTColumn]:
        """Get the columns from the manifest and catalog"""
        manifest_columns = self._property_from_manifest("columns")
        catalog_columns = self._property_from_catalog("columns")
        column_tests = self.get_column_tests_from_manifest()
        return self.extract_columns_from_artifacts(
            manifest_columns, catalog_columns, column_tests
        )

    @property
    def primary_keys(self) -> List[str]:
        """Get the primary keys"""
        model_constraints = self._property_from_manifest("constraints")
        for constraint in model_constraints:
            if constraint.get("type") == ConstraintType.PRIMARY_KEY.value:
                return [x.lower() for x in constraint.get("columns")]
        column_names = []
        for column in self.columns:
            if column.has_primary_key_constraint:
                column_names.append(column.name.lower())
        return column_names

    @property
    def custom_schema(self) -> Optional[str]:
        """Get the custom schema"""
        return self._property_from_manifest("config").get("schema")

    @staticmethod
    def reconcile_custom_target_schema(
        target_schema: str, custom_schema: Optional[str], current_schema: str
    ) -> str:
        """
        Figure out production schema from the CI/dev manifest and config
        https://docs.getdbt.com/docs/build/custom-schemas
        """
        production_target_schema = target_schema
        if custom_schema:
            if not current_schema.endswith(custom_schema):
                # custom schema is not used in this current environment. But production uses it.
                # staging -> production_marketing
                return f"{production_target_schema}_{custom_schema}"
            current_schema_prefix = current_schema.split(custom_schema)[0]
            if current_schema_prefix:
                non_word_suffix = re.search(r"[\-\_]+$", current_schema_prefix)
                if non_word_suffix:
                    # replace target schema to production env
                    # but keep the non-word connector, typically underscore.
                    # staging_marketing -> production_marketing
                    return current_schema.replace(
                        current_schema_prefix,
                        f"{target_schema}{non_word_suffix.group(0)}",
                    )
            # target schema is not prefixed to the custom schema according to DBT setup.
            # marketing -> marketing
            return current_schema
        # No custom schema override so just use the target schema.
        # staging -> production
        return target_schema

    def construct_urn(self) -> str:
        """Construct the urn"""
        return f"{self.project.org_name_snakecase}.dbt.{self.project.name}.{self.name}"

    @classmethod
    def perform_reconciliation_for_datastore_sources(
        cls, sources: List[Dict], custom_schema: Optional[str], current_schema: str
    ) -> Dict:
        """Perform reconciliation for datastores"""
        for source in sources:
            namespace = source.get("data", {}).get("namespace")
            if namespace:
                # some datastores don't have a db.schema namespace but just a schema
                if "." in namespace:
                    database, schema = namespace.split(".")[:2]
                    reconciled = cls.reconcile_custom_target_schema(
                        schema, custom_schema, current_schema
                    )
                    source["data"]["namespace"] = f"{database}.{reconciled}"
                else:
                    source["data"]["namespace"] = cls.reconcile_custom_target_schema(
                        namespace, custom_schema, current_schema
                    )
        return sources

    def construct_datastores(self) -> Dict:
        """Construct the datastores"""
        datastores = (
            construct_dapi_source_sink_from_playbooks(
                self.project.config.playbooks, self.name
            )
            if self.project.config.playbooks
            else {"sources": [], "sinks": []}
        )
        self.perform_reconciliation_for_datastore_sources(
            datastores["sources"], self.custom_schema, self.schema
        )
        return DapiValidator.add_non_playbook_datastore_fields(datastores)

    def construct_owner_team_urn(self) -> Optional[str]:
        """Construct the owner team urn"""
        return (
            construct_owner_team_urn_from_playbooks(
                self.project.config.playbooks, self.name, self.model_path
            )
            if self.project.config.playbooks
            else None
        )


class DbtDapiValidator(DapiValidator[DBTProjectInfo], DBTCloudMixin):
    """
    Validator class for DAPIs created from DBT models

    """

    INTEGRATION_NAME = ORMIntegration.DBT
    INTEGRATION_TYPE = IntegrationType.DBT

    def __init__(self, *, skip_generation: bool, **kwargs):
        self._skip_generation = skip_generation
        head_sha = os.environ.get("GITHUB_HEAD_SHA") or os.environ.get(
            "BUILDKITE_COMMIT"
        )
        self._dbt_commit_sha = kwargs.get("commit_sha") or head_sha
        self._fast_fail = (
            os.environ.get("DAPI_DBT_FAST_FAIL", "false").lower() == "true"
        )
        super().__init__(**kwargs)

    @property
    def _github_pr_number(self) -> Optional[int]:
        """Get the github pr number"""
        return self.change_trigger_event.pull_request_number

    @property
    def _branch_name(self) -> Optional[str]:
        """Get the branch name"""
        return self.change_trigger_event.branch

    def get_all_projects(self) -> List[DBTProjectInfo]:
        """List the DBT projects to generate documentation for"""
        projects = []
        dbt_config_files = find_files_with_suffix(
            self.root_dir,
            [f"/{self.integration_config.artifact_path or DBT_CONFIG_YML}"],
            exclude_dirs=["dbt_packages"],
        )

        for config_full_path in dbt_config_files:
            # glob for a file called dbt_project.yml within the dbt project
            project_full_path = os.path.normpath(os.path.dirname(config_full_path))

            override = ProjectConfig(
                project_path=get_project_path_from_full_path(
                    self.root_dir, project_full_path
                ),
                artifact_path=DBT_ARTIFACTS_DIR,
                include_models=self.integration_config.include_models,
            )

            projects.append(self.get_project(override))

        return projects

    def get_project(self, project_config: ProjectConfig) -> DBTProjectInfo:
        """Given a project config, return ProjectInfo object"""

        copy_project_config = copy.deepcopy(project_config)
        project_full_path = construct_project_full_path(
            self.root_dir, copy_project_config.project_path
        )

        copy_project_config.artifact_path = (
            copy_project_config.artifact_path or DBT_ARTIFACTS_DIR
        )
        copy_project_config.include_models = (
            copy_project_config.include_models or self.integration_config.include_models
        )

        artifact_full_path = os.path.join(
            project_full_path, copy_project_config.artifact_path
        )

        config_full_path = os.path.join(project_full_path, DBT_CONFIG_YML)
        dbt_config = read_yaml_or_json(config_full_path)

        return DBTProjectInfo(
            org_name_snakecase=self.config.org_name_snakecase,
            name=dbt_config["name"],
            dbt_config=dbt_config,
            root_path=self.root_dir,
            config=copy_project_config,
            full_path=os.path.normpath(project_full_path),
            artifact_full_path=artifact_full_path,
        )

    def _sync_from_external_sources(self, projects: List[DBTProjectInfo]) -> None:
        """This function will sync the dbt projects from external sources"""
        logger.info("DBT: About to check external sources for artifacts")
        # We will run through all the external sync functions, in order, till any function
        # returns True
        self.sync_dbt_cloud_artifacts(projects)
        # or self.sync_dbt_snowflake_artifacts(projects)
        # or self.sync_dbt_bigquery_artifacts(projects)

    def _assert_necessary_files_exist(self, projects: List[DBTProjectInfo]) -> None:
        """Assert that the necessary files exist"""

        # just in case, though this really should not be called
        # in this instance
        if self._skip_generation:  # pragma: no cover
            return

        errors = []
        for project in projects:
            try:
                _ = project.manifest
            except FileNotFoundError:
                errors.append(
                    f"Manifest file not found for project {project.name} "
                    f"at {project.full_path}, or was not able to be synced "
                    f"from dbt cloud"
                )

            try:
                _ = project.catalog
            except FileNotFoundError:
                errors.append(
                    f"Catalog file not found for project {project.name} "
                    f"at {project.full_path}, or was not able to be synced "
                    f"from dbt cloud"
                )

        if errors:
            raise FileNotFoundError("\n".join(errors))

    def validate_projects(self, projects: List[DBTProjectInfo]):
        """Verify that all projects and their schema files exist"""
        self._assert_necessary_files_exist(projects)

    @weak_lru_cache(maxsize=8)
    def selected_projects(self, validate: bool = False) -> List[DBTProjectInfo]:
        """Get the selected projects"""

        # Get the projects, but do not validate them yet. If we are using
        # integrations like dbt cloud, we might have to wait till later to
        # ensure all the files are synced
        projects = super().selected_projects(validate=validate)

        # we only download artifacts if we intend to generate
        if self._skip_generation:
            return projects

        # Try getting dbt files from dbt cloud or other sources. If integrated
        # with various other projects, the manifest and catalog files will be
        # synced from those sources.
        self._sync_from_external_sources(projects)

        # Validate that the selected projects exist
        # NOTE: loads stuff into memory
        self.validate_projects(projects)

        return projects

    def _get_dbt_models(self) -> List[DBTModel]:
        """Get the DBT models from manifest.json and enrich with catalog.json"""
        if self._skip_generation:
            raise RuntimeError("Cannot get DBT models when skipping artifact downloads")

        dbt_models = []
        models_missing_in_catalog = []
        projects = self.selected_projects()
        for project in projects:
            for unique_model_name, model in project.manifest["nodes"].items():
                if (
                    model["resource_type"] == "model"
                    and model["config"]["materialized"] != "ephemeral"
                ):
                    if unique_model_name not in project.catalog["nodes"]:
                        # Log a warning if the model is not found in the catalog
                        models_missing_in_catalog.append(unique_model_name)
                        continue
                    dbt_model = DBTModel(
                        name=model["name"],
                        unique_id=unique_model_name,
                        project=project,
                        is_allowlisted=project.is_model_included(
                            model["name"],
                            os.path.join(
                                project.full_path, model["original_file_path"]
                            ),
                        ),
                    )
                    dbt_models.append(dbt_model)
        if models_missing_in_catalog:
            logger.warning(
                "%s models are missing in catalog.json - "
                "please run the following to fix:"
                "\n\n1. dbt run --models %s"
                "\n\n2. dbt docs generate",
                len(models_missing_in_catalog),
                " ".join(models_missing_in_catalog),
            )
        return dbt_models

    @cached_property
    def _base_generated_files_and_generated_metadata(
        self,
    ) -> Tuple[Dict[str, Dict], Dict[str, Optional[Dict]]]:
        """Get the base generated files"""

        # if we need to skip, just fallback to the original file state
        if self._skip_generation:
            logger.info(
                "DBT: skipping source sync, defaulting to original file state",
                extra={
                    "commit_sha": self._dbt_commit_sha,
                    "head_sha": os.environ.get("GITHUB_HEAD_SHA")
                    or os.environ.get("BUILDKITE_COMMIT"),
                },
            )
            return {
                fp: dapi
                for project in self.selected_projects()
                for fp, dapi in project.filter_dapis(self.original_file_state).items()
            }, {}

        base_generated_files = {}
        generated_metadata = {}
        for table in self._get_dbt_models():
            if table.is_allowlisted:
                dapi_location = table.project.construct_dapi_location(table.name)

                context = {
                    "service": table.project.name,
                    "integration": "dbt",
                    "rel_model_path": os.path.relpath(
                        table.model_path,
                        os.path.dirname(dapi_location),
                    ),
                }
                if table.doc_path:
                    context["rel_doc_path"] = os.path.relpath(
                        table.doc_path,
                        os.path.dirname(dapi_location),
                    )

                base_generated_files[dapi_location] = (
                    self.add_default_non_generated_schema_portions(
                        {
                            "urn": table.construct_urn(),
                            "description": table.manifest_table_description or None,
                            "owner_team_urn": table.construct_owner_team_urn(),
                            "datastores": table.construct_datastores(),
                            "fields": [field.for_dapi() for field in table.columns],
                            "primary_key": table.primary_keys,
                            "context": context,
                        }
                    )
                )
                generated_metadata[dapi_location] = {
                    "custom_schema": table.custom_schema,
                    "current_schema": table.schema,
                }
        return base_generated_files, generated_metadata

    def _get_additional_metadata_from_generated(self, filepath: str) -> Optional[Dict]:
        """Get the additional metadata from the generated"""
        return self._base_generated_files_and_generated_metadata[1].get(filepath)

    def _get_base_generated_files(self) -> Dict[str, Dict]:
        """Get the base generated files"""
        return self._base_generated_files_and_generated_metadata[0]

    @property
    def _generate_skipped(self) -> bool:
        """Check if generation is skipped"""
        return self._skip_generation
