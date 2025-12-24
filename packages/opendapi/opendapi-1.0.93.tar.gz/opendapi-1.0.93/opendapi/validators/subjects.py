"""Teams validator module"""

from collections import Counter
from typing import Dict, List, Tuple, Union

from opendapi.defs import OPENDAPI_SPEC_URL, SUBJECTS_SUFFIX, OpenDAPIEntity
from opendapi.validators.base import (
    BaseValidator,
    MultiValidationError,
    ValidationError,
)
from opendapi.validators.defs import FileSet, MergeKeyCompositeIDParams
from opendapi.weakref import weak_lru_cache


class SubjectsValidator(BaseValidator):
    """
    Validator class for Subjects files
    """

    SUFFIX = SUBJECTS_SUFFIX
    SPEC_VERSION = "0-0-1"
    ENTITY = OpenDAPIEntity.SUBJECTS

    MUST_GENERATE_EVEN_IF_ENTITY_TYPE_EXISTS = False

    # Paths & keys to use for uniqueness check within a list of dicts when merging
    MERGE_UNIQUE_LOOKUP_KEYS: List[
        Tuple[
            List[Union[str, int, MergeKeyCompositeIDParams.IgnoreListIndexType]],
            MergeKeyCompositeIDParams,
        ]
    ] = [
        (["subjects"], MergeKeyCompositeIDParams(required=[["urn"]])),
        (
            [
                "subjects",
                MergeKeyCompositeIDParams.IGNORE_LIST_INDEX,
                "category_mapping",
            ],
            MergeKeyCompositeIDParams(required=[["category_urn"]]),
        ),
    ]

    @weak_lru_cache()
    def _get_file_state_subject_urn_counts(self, fileset: FileSet) -> Counter:
        """Collect all the subject urns"""
        return Counter(
            (
                subject.get("urn")
                for content in self.get_file_state(fileset).values()
                for subject in content.get("subjects", [])
            )
        )

    def _validate_subject_urns_globally_unique(
        self, file: str, content: dict, fileset: FileSet
    ):
        """Validate if the subject urns are globally unique"""
        subject_urn_counts = self._get_file_state_subject_urn_counts(fileset)
        non_unique_subject_urns = {
            subject["urn"]
            for subject in content.get("subjects", [])
            if subject_urn_counts[subject["urn"]] > 1
        }
        if non_unique_subject_urns:
            raise ValidationError(
                f"Non-globally-unique subject urns in file '{file}': {non_unique_subject_urns}"
            )

    def _validate_intra_mapping_category_urns_unique(self, file: str, content: dict):
        """Validate if the mapped category urns are unique within a subjects file"""

        errors = []
        for subject in content.get("subjects", []):
            category_urns_count = Counter(
                mapping["category_urn"]
                for mapping in subject.get("category_mapping", [])
            )
            non_unique_category_urns = {
                category_urn
                for category_urn, count in category_urns_count.items()
                if count > 1
            }
            if non_unique_category_urns:
                errors.append(
                    f"Subject '{subject['urn']}' has repeat category_urn "
                    f"in its mapping: {non_unique_category_urns}"
                )

        if errors:
            raise MultiValidationError(
                errors,
                f"Non-unique category urns for subjects in file '{file}'",
            )

    def _is_personal_data_is_direct_identifier_matched(self, file: str, content: dict):
        """Validate that you cannot have a direct identifier without it also being personal data"""

        errors = []
        for subject in content.get("subjects", []):
            for mapping in subject.get("category_mapping", []):
                if mapping.get("is_direct_identifier") and not mapping.get(
                    "is_personal_data"
                ):
                    errors.append(
                        (
                            f"Mapping for subject '{subject['urn']}' and category "
                            f"'{mapping['category_urn']}' has a direct identifier "
                            "that is not personal data, which is invalid"
                        )
                    )

        if errors:
            raise MultiValidationError(
                errors,
                f"Mismatched personal data designations for mappings in '{file}'",
            )

    def validate_content(self, file: str, content: Dict, fileset: FileSet):
        """Validate the content of the files"""
        super().validate_content(file, content, fileset)
        self._validate_subject_urns_globally_unique(file, content, fileset)
        self._validate_intra_mapping_category_urns_unique(file, content)
        self._is_personal_data_is_direct_identifier_matched(file, content)

    def _get_base_generated_files(self) -> Dict[str, Dict]:
        """Set Autoupdate templates in {file_path: content} format"""
        return {
            f"{self.base_destination_dir}/{self.config.org_name_snakecase}.subjects.yaml": {
                "schema": OPENDAPI_SPEC_URL.format(
                    version=self.SPEC_VERSION, entity="subjects"
                ),
                "subjects": [],
            }
        }
