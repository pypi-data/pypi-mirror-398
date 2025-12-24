"""DAPI validator module"""

from __future__ import annotations

from abc import abstractmethod
from typing import Dict, Generic, List

from opendapi.logging import logger
from opendapi.validators.dapi.base.main import DapiValidator, ProjectInfoType
from opendapi.validators.dapi.models import ProjectInfo
from opendapi.validators.defs import IntegrationType


class RuntimeDapiValidator(DapiValidator[ProjectInfoType], Generic[ProjectInfoType]):
    """
    Abstract validator class for Runtime-integration DAPI files
    """

    INTEGRATION_TYPE: IntegrationType = IntegrationType.RUNTIME

    def __init__(self, *, skip_generation, **kwargs):
        self._skip_generation = skip_generation
        super().__init__(**kwargs)

    @abstractmethod
    def _unskipped_validate_projects(self, projects: List[ProjectInfo]):
        """Validate the projects"""

    def _skipped_validate_projects(self, projects: List[ProjectInfo]):
        """Validate the projects"""
        # Possible that the project and artifacts may not exist if we are skipping generation

    def validate_projects(self, projects: List[ProjectInfo]):
        """Validate the projects"""
        # Possible that the project and artifacts may not exist if we are skipping generation
        if self._skip_generation:
            return self._skipped_validate_projects(projects)

        return self._unskipped_validate_projects(projects)

    @abstractmethod
    def _unskipped_get_base_generated_files(self) -> Dict[str, Dict]:
        """Build the base template for autoupdate"""

    def _skipped_get_base_generated_files(self) -> Dict[str, Dict]:
        """Build the base template for autoupdate"""
        return self.original_file_state

    def _get_base_generated_files(self) -> Dict[str, Dict]:
        """Build the base template for autoupdate"""
        if self._skip_generation:
            logger.info(
                (
                    "Skipping generation of DAPI files for runtime ORM integration, "
                    "falling back to current DAPI file state."
                ),
                extra={
                    "validator": type(self).__name__,
                },
            )
            return self._skipped_get_base_generated_files()

        return self._unskipped_get_base_generated_files()

    @property
    def _generate_skipped(self) -> bool:
        """Return True if generation is skipped"""
        return self._skip_generation
