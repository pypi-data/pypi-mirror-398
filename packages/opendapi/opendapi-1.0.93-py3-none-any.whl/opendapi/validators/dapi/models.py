"""Common models for use by dapi validators"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from opendapi.adapters.file import text_file_loader
from opendapi.config import (
    construct_project_full_path,
    get_project_path_from_full_path,
    is_model_in_allowlist,
)
from opendapi.models import ProjectConfig
from opendapi.selector import filter_candidates_by_selectors


@dataclass
class ProjectInfo:
    """Data class for project related information"""

    # Organization name in snakecase
    org_name_snakecase: str

    # The main project config
    config: ProjectConfig

    # Root directory of the checked out local repository
    root_path: str

    # Full path of the project in the checked out local storage
    full_path: str
    artifact_full_path: Optional[str] = None

    def construct_dapi_location(self, table_name: str) -> str:
        """Construct the location of the DAPI file within a project"""
        return f"{self.full_path}/dapis/{table_name}.dapi.yaml"

    def filter_dapis(self, dapis: Dict[str, Dict]) -> Dict[str, Dict]:
        """Get the owned DAPIs"""
        return {
            filepath: dapi
            for filepath, dapi in dapis.items()
            if filepath.startswith(self.full_path)
        }

    def is_model_included(self, model_name: str, model_abspath: str) -> bool:
        """Check if the model is included"""
        filtered = self.filter_included_models([(model_name, model_abspath)])
        return len(filtered) > 0

    def filter_included_models(
        self,
        model_name_abspaths: List[Tuple[str, str]],
    ) -> List[Tuple[str, str]]:
        """Check if the model is included"""
        if self.config.include_models:
            # We want the path regex to be relative to the root path
            model_name_relpaths = [
                (
                    model_name,
                    get_project_path_from_full_path(self.root_path, model_abspath),
                )
                for model_name, model_abspath in model_name_abspaths
            ]
            filtered_model_names_by_path = filter_candidates_by_selectors(
                model_name_relpaths,
                self.config.include_models,
                file_loader=lambda rel_path: text_file_loader(
                    os.path.join(self.root_path, rel_path)
                ),
                include_all_if_unspecified=True,
            )
            return [
                (model_name, construct_project_full_path(self.root_path, model_path))
                for model_name, model_path in filtered_model_names_by_path
            ]

        if self.config.model_allowlist:
            return [
                (model_name, model_abspath)
                # is_model_in_allowlist expects the model path to be absolute
                for model_name, model_abspath in model_name_abspaths
                if is_model_in_allowlist(
                    model_name, model_abspath, self.config.model_allowlist
                )
            ]

        return model_name_abspaths


@dataclass
class PackageScopedProjectInfo(ProjectInfo):
    """Project info for package scoped DAPI validators"""

    file_contents: Optional[Dict] = field(default_factory=dict)
