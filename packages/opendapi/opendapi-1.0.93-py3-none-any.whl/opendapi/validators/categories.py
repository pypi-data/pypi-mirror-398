"""Teams validator module"""

from collections import Counter
from typing import Dict, List, Tuple, Union

from opendapi.defs import CATEGORIES_SUFFIX, OPENDAPI_SPEC_URL, OpenDAPIEntity
from opendapi.validators.base import BaseValidator, ValidationError
from opendapi.validators.defs import FileSet, MergeKeyCompositeIDParams
from opendapi.weakref import weak_lru_cache


class CategoriesValidator(BaseValidator):
    """
    Validator class for Subjects files
    """

    SUFFIX = CATEGORIES_SUFFIX
    SPEC_VERSION = "0-0-1"
    ENTITY = OpenDAPIEntity.CATEGORIES

    MUST_GENERATE_EVEN_IF_ENTITY_TYPE_EXISTS = False

    # Paths & keys to use for uniqueness check within a list of dicts when merging
    MERGE_UNIQUE_LOOKUP_KEYS: List[
        Tuple[
            List[Union[str, int, MergeKeyCompositeIDParams.IgnoreListIndexType]],
            MergeKeyCompositeIDParams,
        ]
    ] = [(["categories"], MergeKeyCompositeIDParams(required=[["urn"]]))]

    @weak_lru_cache()
    def _get_file_state_category_urn_counts(self, fileset: FileSet) -> Counter:
        """Collect all the category urns"""
        return Counter(
            (
                category.get("urn")
                for content in self.get_file_state(fileset).values()
                for category in content.get("categories", [])
            )
        )

    def _validate_period_delimited_taxonomical_structure(
        self, file: str, content: dict, fileset: FileSet
    ):
        """Validate if the category urns are period delimited"""
        category_urns = set(self._get_file_state_category_urn_counts(fileset).keys())
        invalid_categories = {
            category["urn"]
            for category in content.get("categories", [])
            # parent does not exist
            if category["urn"].rsplit(".", 1)[0] not in category_urns
        }
        if invalid_categories:
            raise ValidationError(
                (
                    "Category URNs that do not have parents in the taxonomy as defined by the "
                    f"period delimited structure found in file '{file}': {invalid_categories}"
                )
            )

    def _validate_category_urns_globally_unique(
        self, file: str, content: dict, fileset: FileSet
    ):
        """Validate if the category urns are globally unique"""
        category_urn_counts = self._get_file_state_category_urn_counts(fileset)
        non_unique_category_urns = {
            category["urn"]
            for category in content.get("categories", [])
            if category_urn_counts[category["urn"]] > 1
        }
        if non_unique_category_urns:
            raise ValidationError(
                f"Non-globally-unique category urns in file '{file}': {non_unique_category_urns}"
            )

    def validate_content(self, file: str, content: Dict, fileset: FileSet):
        """Validate the content of the files"""
        super().validate_content(file, content, fileset)
        self._validate_period_delimited_taxonomical_structure(file, content, fileset)
        self._validate_category_urns_globally_unique(file, content, fileset)

    def _get_base_generated_files(self) -> Dict[str, Dict]:
        """Set Autoupdate templates in {file_path: content} format"""
        return {
            f"{self.base_destination_dir}/{self.config.org_name_snakecase}.categories.yaml": {
                "schema": OPENDAPI_SPEC_URL.format(
                    version=self.SPEC_VERSION, entity="categories"
                ),
                "categories": [],
            }
        }
