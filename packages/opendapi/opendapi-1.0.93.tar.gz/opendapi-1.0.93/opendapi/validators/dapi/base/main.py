"""DAPI validator module"""

from __future__ import annotations

import copy
import os
from abc import abstractmethod
from collections import Counter
from functools import cached_property
from typing import Dict, Generic, List, Tuple, Type, TypeVar, Union

from opendapi.adapters.file import text_file_loader
from opendapi.cli.utils import load_missing_dapis_from_cache
from opendapi.config import get_project_path_from_full_path
from opendapi.defs import DAPI_SUFFIX, OPENDAPI_SPEC_URL, OpenDAPIEntity, ORMIntegration
from opendapi.models import (
    ConfigParam,
    IntegrationConfig,
    PlaybookConfig,
    ProjectConfig,
)
from opendapi.selector import filter_candidates_by_selectors
from opendapi.utils import sort_dapi_fields
from opendapi.validators.base import (
    BaseValidator,
    MultiValidationError,
    ValidationError,
)
from opendapi.validators.dapi.models import ProjectInfo
from opendapi.validators.defs import FileSet, MergeKeyCompositeIDParams

ProjectInfoType = TypeVar(  # pylint: disable=invalid-name
    "ProjectInfoType", bound=ProjectInfo
)


class BaseDapiValidator(BaseValidator):
    """
    Abstract base validator class for DAPI files
    """

    INTEGRATION_NAME: ORMIntegration = NotImplementedError
    SUFFIX = DAPI_SUFFIX
    SPEC_VERSION = "0-0-1"
    ENTITY = OpenDAPIEntity.DAPI

    MUST_GENERATE_EVEN_IF_ENTITY_TYPE_EXISTS = True

    # Paths & keys to use for uniqueness check within a list of dicts when merging
    MERGE_UNIQUE_LOOKUP_KEYS: List[
        Tuple[
            List[Union[str, int, MergeKeyCompositeIDParams.IgnoreListIndexType]],
            MergeKeyCompositeIDParams,
        ]
    ] = [
        (
            ["fields"],
            MergeKeyCompositeIDParams(required=[["name"], ["data_type"]]),
        ),
        (
            ["datastores", "sources"],
            MergeKeyCompositeIDParams(
                required=[["urn"]],
                optional=[
                    ["data", "namespace"],
                    ["data", "identifier"],
                    ["data", "replication_config_urn"],
                ],
            ),
        ),
        (
            ["datastores", "sinks"],
            MergeKeyCompositeIDParams(
                required=[["urn"]],
                optional=[
                    ["data", "namespace"],
                    ["data", "identifier"],
                    ["data", "replication_config_urn"],
                ],
            ),
        ),
        # this is less for merging and more for deduping, but merging would be fine
        # as well
        (
            [
                "fields",
                MergeKeyCompositeIDParams.IGNORE_LIST_INDEX,
                "data_subjects_and_categories",
            ],
            MergeKeyCompositeIDParams(required=[["subject_urn"], ["category_urn"]]),
        ),
    ]

    # Paths to disallow new entries when merging
    MERGE_DISALLOW_NEW_ENTRIES_PATH: List[List[str]] = [["fields"]]

    _REGISTRY: Dict[ORMIntegration, Type[BaseDapiValidator]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # another base class
        if cls.INTEGRATION_NAME in (NotImplementedError, NotImplemented):
            return

        if cls.INTEGRATION_NAME in cls._REGISTRY:  # pragma: nocover
            raise ValueError(f"Integration {cls.INTEGRATION_NAME} already registered")

        cls._REGISTRY[cls.INTEGRATION_NAME] = cls

    @staticmethod
    def get_validator(integration_name: ORMIntegration) -> Type[BaseDapiValidator]:
        """Get the validator for the integration"""
        return BaseDapiValidator._REGISTRY[integration_name]

    def _get_field_names(self, content: dict) -> List[str]:
        """Get the field names"""
        return [field["name"] for field in content["fields"]]

    def _retention_reference_is_a_valid_field(self, file: str, content: Dict):
        """Validate if the retention reference is a valid field"""
        retention_reference = content.get("retention_reference")
        if retention_reference and retention_reference not in self._get_field_names(
            content
        ):
            raise ValidationError(
                f"Retention reference '{retention_reference}' not a valid field in '{file}'"
            )

    def _validate_primary_key_is_a_valid_field(self, file: str, content: Dict):
        """Validate if the primary key is a valid field"""
        primary_key = content.get("primary_key") or []
        field_names = self._get_field_names(content)
        for key in primary_key:
            if key not in field_names:
                raise ValidationError(
                    f"Primary key element '{key}' not a valid field in '{file}'"
                )

    def _validate_field_names_unique(self, file: str, content: Dict):
        """Validate if the field names are unique"""
        field_names = self._get_field_names(content)
        duplicates = {name for name in field_names if field_names.count(name) > 1}
        if duplicates:
            raise ValidationError(
                f"Field names must be unique in '{file}'"
                f"Duplicate field names: {duplicates}"
            )

    def _validate_field_data_subjects_and_categories_unique(
        self, file: str, content: Dict
    ):
        """Validate if the field data subjects and categories are unique"""
        errors = []
        for field in content.get("fields", []):
            data_subjects_and_categories_counts = Counter(
                (subj_and_cat["subject_urn"], subj_and_cat["category_urn"])
                for subj_and_cat in field.get("data_subjects_and_categories", [])
            )
            non_unique_data_subjects_and_categories = {
                subj_and_cat
                for subj_and_cat, count in data_subjects_and_categories_counts.items()
                if count > 1
            }
            if non_unique_data_subjects_and_categories:
                errors.append(
                    (
                        f"In file '{file}', the following 'data_subjects_and_categories' pairs are "
                        f"repeated in field '{field['name']}': "
                        f"{non_unique_data_subjects_and_categories}"
                    )
                )
        if errors:
            raise MultiValidationError(
                errors, "Non-unique data subjects and categories pairs within fields"
            )

    def _is_personal_data_is_direct_identifier_matched(self, file: str, content: dict):
        """Validate that you cannot have a direct identifier without it also being personal data"""

        errors = []
        for field in content.get("fields", []):
            if field.get("is_direct_identifier") and not field.get("is_personal_data"):
                errors.append(
                    f"Field '{field['name']}' in file '{file}' is a direct identifier "
                    "but not marked as personal data"
                )

        if errors:
            raise MultiValidationError(
                errors,
                f"Mismatched personal data designations for mappings in '{file}'",
            )

    @cached_property
    def integration_config(self) -> IntegrationConfig:
        """Get the config for this integration"""
        integration_config = copy.deepcopy(
            self.config.get_integration_config(self.INTEGRATION_NAME, self.runtime)
        )

        override_config = integration_config.get(ConfigParam.PROJECTS.value, {}).get(
            ConfigParam.OVERRIDES.value, []
        )

        overrides = []
        for override in override_config:
            playbooks = [
                PlaybookConfig.from_dict(playbook)
                for playbook in override.get(ConfigParam.PLAYBOOKS.value, [])
            ]
            override[ConfigParam.PLAYBOOKS.value] = playbooks
            overrides.append(ProjectConfig.from_dict(override))

        integration_config[ConfigParam.PROJECTS.value][
            ConfigParam.OVERRIDES.value
        ] = overrides

        return IntegrationConfig.from_dict(
            integration_config[ConfigParam.PROJECTS.value]
        )

    def validate_content(self, file: str, content: Dict, fileset: FileSet):
        """Validate the content of the files"""
        super().validate_content(file, content, fileset)
        self._validate_primary_key_is_a_valid_field(file, content)
        self._validate_field_data_subjects_and_categories_unique(file, content)
        self._is_personal_data_is_direct_identifier_matched(file, content)
        self._validate_field_names_unique(file, content)
        self._retention_reference_is_a_valid_field(file, content)

    @property
    def base_destination_dir(self) -> str:
        return self.root_dir

    def filter_dapis(self, dapis: Dict[str, Dict]) -> Dict[str, Dict]:
        """Get the owned DAPIs"""
        return {
            file: content
            for file, content in dapis.items()
            # we want the BaseDapiValidator to be able to collect all Dapis
            # but all impls of BaseDapiValidator should only validate their own
            # integration
            # then, we want to match integrations directly, but if an integration is missing,
            # then we want to collect it with the fallback validator
            if (
                type(self) is BaseDapiValidator  # pylint: disable=unidiomatic-typecheck
                or (integration := content.get("context", {}).get("integration"))
                == self.INTEGRATION_NAME.value  # pylint: disable=no-member
                or not integration
                and self.INTEGRATION_NAME is ORMIntegration.NO_ORM_FALLBACK
            )
        }

    @cached_property
    def original_file_state(self) -> Dict[str, Dict]:
        """
        Get the contents of all files in the root directory,
        if they are part of the integration
        """
        _og_dapis = self._get_file_contents_for_suffix(self.SUFFIX)
        # NOTE: we must prefix with root dir here
        dapis = {
            os.path.join(self.root_dir, filepath): dapi
            for filepath, dapi in load_missing_dapis_from_cache().items()
        }
        # NOTE: revert to dapis.update(_og_dapis)
        _problem_dapi_filepath_suffixes = (
            "/routing_number_validations.dapi.yaml",
            "/versions.dapi.yaml",
        )
        for filepath, dapi in _og_dapis.items():
            if filepath.endswith(_problem_dapi_filepath_suffixes):  # pragma: nocover
                continue

            dapis[filepath] = dapi

        og_file_state = self.filter_dapis(dapis)
        # Temporary fix for historical_ept_rates
        # KB Note: remove this once the bug is fixed
        for dapi in og_file_state.values():
            if dapi.get("urn", "").endswith("historical_ept_rates"):  # pragma: nocover
                seen_fields = set()
                deduped_fields = []
                for field in dapi["fields"]:
                    if field["name"] not in seen_fields:
                        deduped_fields.append(field)
                        seen_fields.add(field["name"])
                dapi["fields"] = deduped_fields

        # lets sort the fields for original just as we do
        # for generated making comparisons easier
        for dapi in og_file_state.values():
            dapi["fields"] = sort_dapi_fields(dapi["fields"])

        # NOTE: CLEANUP - lets remove is_pii, access from each field
        for dapi in og_file_state.values():
            for field in dapi["fields"]:
                field.pop("is_pii", None)
                field.pop("access", None)

        return og_file_state

    @cached_property
    def generated_file_state(self) -> Dict[str, Dict]:
        """Get the generated file state"""
        gen_files = super().generated_file_state
        # we will sort the fields for generated so that nested
        # fields are clustered in a coherent way
        for dapi in gen_files.values():
            dapi["fields"] = sort_dapi_fields(dapi["fields"])

        # NOTE: CLEANUP - lets remove is_pii, access from each field
        for dapi in gen_files.values():
            for field in dapi["fields"]:
                field.pop("is_pii", None)
                field.pop("access", None)

        return gen_files

    @staticmethod
    def add_non_playbook_datastore_fields(
        datastores: dict,
    ) -> dict:
        """Add non-playbook fields to the datastores"""
        for ds_type in ["sources", "sinks"]:
            for ds in datastores.get(ds_type, []):
                ds["business_purposes"] = []
                ds["retention_days"] = None
        return datastores

    @classmethod
    def add_default_non_generated_schema_portions(cls, dapi: dict) -> dict:
        """Add the default schema portion to the dapi"""
        dapi["fields"] = [
            {
                "description": None,
                "data_subjects_and_categories": [],
                "sensitivity_level": None,
                "is_personal_data": None,
                "is_direct_identifier": None,
                **field,
            }
            for field in dapi["fields"]
        ]
        return {
            "schema": OPENDAPI_SPEC_URL.format(version=cls.SPEC_VERSION, entity="dapi"),
            "type": "entity",
            "owner_team_urn": None,
            "datastores": DapiValidator.add_non_playbook_datastore_fields(
                {
                    "sources": [],
                    "sinks": [],
                }
            ),
            "description": None,
            "privacy_requirements": {
                "dsr_access_endpoint": None,
                "dsr_deletion_endpoint": None,
            },
            "context": {},
            **dapi,
        }

    def _get_base_generated_files(self) -> Dict[str, Dict]:
        """Set Autoupdate templates in {file_path: content} format"""
        return {
            f"{self.base_destination_dir}/sample_dataset.dapi.yaml": {
                "schema": OPENDAPI_SPEC_URL.format(
                    version=self.SPEC_VERSION, entity="dapi"
                ),
                "urn": "my_company.sample.dataset",
                "type": "entity",
                "description": "Sample dataset that shows how DAPI is created",
                "owner_team_urn": "my_company.sample.team",
                "datastores": {
                    "sources": [
                        {
                            "urn": "my_company.sample.datastore_1",
                            "data": {
                                "identifier": "sample_dataset",
                                "namespace": "sample_db.sample_schema",
                            },
                            "business_purposes": [],
                            "retention_days": None,
                        }
                    ],
                    "sinks": [
                        {
                            "urn": "my_company.sample.datastore_2",
                            "data": {
                                "identifier": "sample_dataset",
                                "namespace": "sample_db.sample_schema",
                            },
                            "business_purposes": [],
                            "retention_days": None,
                        }
                    ],
                },
                "fields": [
                    {
                        "name": "field1",
                        "data_type": "string",
                        "description": "Sample field 1 in the sample dataset",
                        "is_nullable": False,
                        "is_pii": False,
                        "access": "public",
                        "data_subjects_and_categories": [],
                        "sensitivity_level": None,
                        "is_personal_data": None,
                        "is_direct_identifier": None,
                    }
                ],
                "primary_key": ["field1"],
                "context": {
                    "integration": "custom_dapi",
                },
                "privacy_requirements": {
                    "dsr_access_endpoint": None,
                    "dsr_deletion_endpoint": None,
                },
            }
        }

    @classmethod
    def merge(cls, base: Dict, nxt: Dict) -> Dict:
        """Merge the base and next dictionaries"""
        # NOTE: this is a hack to allow for in flight PRs that have the diverged
        #       dapis to go through merging without considering data type
        if base.get("urn", "").rsplit(".", 1)[-1] in (
            "boms",
            "catalog_item_inventory_snapshots",
            "end_of_month_adjustments",
            "milestones",
            "onboarding_flows",
            "shopify_inventory_items",
            "shopify_product_images",
            "shopify_product_options",
            "shopify_product_variants",
            "shopify_products",
            "trackstar_inventory_snapshots",
            "weighted_average_costs",
        ):
            merge_unique_lookup_keys_override = copy.deepcopy(
                cls.MERGE_UNIQUE_LOOKUP_KEYS
            )
            for i, (path, _) in enumerate(merge_unique_lookup_keys_override):
                if path == ["fields"]:
                    merge_unique_lookup_keys_override[i] = (
                        path,
                        MergeKeyCompositeIDParams(required=[["name"]]),
                    )
        else:
            merge_unique_lookup_keys_override = None

        return cls._get_merger(merge_unique_lookup_keys_override).merge(
            copy.deepcopy(base), copy.deepcopy(nxt)
        )


class DapiValidator(BaseDapiValidator, Generic[ProjectInfoType]):
    """
    Abstract validator class for DAPI files
    """

    def selected_projects(self, validate: bool = True) -> List[ProjectInfoType]:
        """Get the selected projects"""
        projects_by_fullpath: Dict[str, ProjectInfoType] = {}

        if (
            self.integration_config.include_all
            or self.integration_config.include_projects
        ):
            for project in self.get_all_projects():
                projects_by_fullpath[project.full_path] = project

        for override in self.integration_config.overrides:
            project = self.get_project(override)
            projects_by_fullpath[project.full_path] = project

        projects: List[ProjectInfoType] = list(projects_by_fullpath.values())
        project_rel_paths = [
            get_project_path_from_full_path(self.root_dir, project.full_path)
            for project in projects
        ]

        filtered_project_paths = filter_candidates_by_selectors(
            project_rel_paths,
            self.integration_config.include_projects,
            file_loader=lambda rel_path: text_file_loader(
                os.path.join(self.root_dir, rel_path)
            ),
            include_all_if_unspecified=True,
        )

        filtered_projects = [
            proj
            for proj in projects
            if get_project_path_from_full_path(self.root_dir, proj.full_path)
            in filtered_project_paths
        ]

        if validate:
            self.validate_projects(filtered_projects)

        return filtered_projects

    def assert_artifact_files_exist(self, projects: List[ProjectInfoType]):
        """Assert that the artifact files exist"""
        errors = []
        for project in projects:
            artifact_paths = project.artifact_full_path.split(",")
            for artifact_path in artifact_paths:
                if not os.path.exists(artifact_path):
                    errors.append(
                        f"Artifact file {artifact_path} not found for project {project.full_path}"
                    )
        if errors:
            raise FileNotFoundError("\n".join(errors))

    @abstractmethod
    def get_all_projects(self) -> List[ProjectInfoType]:
        """Generate a list of all projects that this validator should check"""

    @abstractmethod
    def get_project(self, project_config: ProjectConfig) -> ProjectInfoType:
        """Given a project config, return an ProjectInfo object"""

    @abstractmethod
    def validate_projects(self, projects: List[ProjectInfoType]):
        """Validate the projects"""

    def filter_dapis(self, dapis: Dict[str, Dict]) -> Dict[str, Dict]:
        """Filter the dapis with projects as well"""
        integration_filtered_dapis = super().filter_dapis(dapis)
        projects = self.selected_projects()
        return {
            fp: dapi
            for project in projects
            for fp, dapi in project.filter_dapis(integration_filtered_dapis).items()
        }
