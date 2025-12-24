"""Teams validator module"""

from collections import Counter
from typing import Dict, List, Tuple, Union

from opendapi.defs import OPENDAPI_SPEC_URL, TEAMS_SUFFIX, OpenDAPIEntity
from opendapi.validators.base import BaseValidator, ValidationError
from opendapi.validators.defs import FileSet, MergeKeyCompositeIDParams
from opendapi.weakref import weak_lru_cache


class TeamsValidator(BaseValidator):
    """
    Validator class for Teams files
    """

    SUFFIX = TEAMS_SUFFIX
    SPEC_VERSION = "0-0-2"
    ENTITY = OpenDAPIEntity.TEAMS

    MUST_GENERATE_EVEN_IF_ENTITY_TYPE_EXISTS = False

    # Paths & keys to use for uniqueness check within a list of dicts when merging
    MERGE_UNIQUE_LOOKUP_KEYS: List[
        Tuple[
            List[Union[str, int, MergeKeyCompositeIDParams.IgnoreListIndexType]],
            MergeKeyCompositeIDParams,
        ]
    ] = [(["teams"], MergeKeyCompositeIDParams(required=[["urn"]]))]

    @weak_lru_cache()
    def _get_file_state_team_urn_counts(self, fileset: FileSet) -> Counter:
        """Collect all the team urns and their counts"""
        return Counter(
            (
                team["urn"]
                for content in self.get_file_state(fileset).values()
                for team in content.get("teams", [])
            )
        )

    def _validate_period_delimited_taxonomical_structure(
        self, file: str, content: dict, fileset: FileSet
    ):
        """Validate if the team urns are period delimited"""
        team_urns = set(self._get_file_state_team_urn_counts(fileset).keys())
        invalid_teams = {
            team["urn"]
            for team in content.get("teams", [])
            # parent does not exist
            if team["urn"].rsplit(".", 1)[0] not in team_urns
        }
        if invalid_teams:
            raise ValidationError(
                (
                    "Team URNs that do not have parents in the taxonomy as defined by the "
                    f"period delimited structure found in file '{file}': {invalid_teams}"
                )
            )

    def _validate_parent_team_urn(self, file: str, content: dict, fileset: FileSet):
        """Validate if the parent team urn is valid"""
        team_urns = set(self._get_file_state_team_urn_counts(fileset).keys())
        teams = content.get("teams") or []
        for team in teams:
            if team.get("parent_team_urn") and team["parent_team_urn"] not in team_urns:
                raise ValidationError(
                    f"Parent team urn '{team['parent_team_urn']}'"
                    f" not found in '{team['urn']}' in '{file}'"
                )

    def _validate_team_urns_globally_unique(
        self, file: str, content: dict, fileset: FileSet
    ):
        """Validate if the team urns are globally unique"""
        team_urn_counts = self._get_file_state_team_urn_counts(fileset)
        non_unique_team_urns = {
            team["urn"]
            for team in content.get("teams", [])
            if team_urn_counts[team["urn"]] > 1
        }
        if non_unique_team_urns:
            raise ValidationError(
                f"Non-globally-unique team urns in file '{file}': {non_unique_team_urns}"
            )

    def validate_content(self, file: str, content: Dict, fileset: FileSet):
        """Validate the content of the files"""
        super().validate_content(file, content, fileset)
        self._validate_team_urns_globally_unique(file, content, fileset)
        # NOTE: 0-0-1 spec did not have the period delimited taxonomical structure
        #       so we need to validate the parent team urns for backwards compatibility
        legacy_spec_schema = OPENDAPI_SPEC_URL.format(version="0-0-1", entity="teams")
        if content["schema"] == legacy_spec_schema:
            self._validate_parent_team_urn(file, content, fileset)
        else:
            self._validate_period_delimited_taxonomical_structure(
                file, content, fileset
            )

    def _get_base_generated_files(self) -> Dict[str, Dict]:
        """Set Autoupdate templates in {file_path: content} format"""
        return {
            f"{self.base_destination_dir}/{self.config.org_name_snakecase}.teams.yaml": {
                "schema": OPENDAPI_SPEC_URL.format(
                    version=self.SPEC_VERSION, entity="teams"
                ),
                "organization": {"name": self.config.org_name},
                "teams": [],
            }
        }
