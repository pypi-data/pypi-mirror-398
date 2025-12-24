"""DAPI validator module"""

from typing import Dict, Optional

from opendapi.validators.dapi.base.main import BaseDapiValidator, ORMIntegration
from opendapi.validators.defs import FileSet


class FallbackDapiValidator(BaseDapiValidator):
    """
    Validator class used to accumulate Dapis for which there are no ORM integrations,
    just so that their Dapi files are known for downstream purposes, if necessary
    """

    INTEGRATION_NAME = ORMIntegration.NO_ORM_FALLBACK

    def validate_existance_at(self, override: Optional[FileSet] = None):
        """
        Validate that the files exist

        NOTE: Since this is a fallback that always runs, we don't expect to find any files,
              so we don't raise any errors here
        """
        return

    def _get_base_generated_files(self) -> Dict[str, Dict]:
        return self.original_file_state
