"""Writers"""

import os
from typing import Dict, List, Optional, Tuple

from opendapi.config import OpenDAPIConfig
from opendapi.utils import YAML, fetch_schema, sorted_yaml_dump
from opendapi.validators.defs import CollectedFile


class BaseFileWriter:
    """Base Writer class for DAPI and related files"""

    def __init__(
        self,
        root_dir: str,
        collected_files: Dict[str, CollectedFile],
        override_config: OpenDAPIConfig = None,
        base_collected_files: Optional[Dict[str, CollectedFile]] = None,
        always_write: bool = False,
    ):
        self.yaml = YAML()
        self.root_dir = root_dir
        self.collected_files = collected_files
        self.config: OpenDAPIConfig = override_config or OpenDAPIConfig(root_dir)
        self.base_collected_files = base_collected_files or {}
        self.always_write = always_write

    @staticmethod
    def _should_process_file(
        collected_file: CollectedFile,
        base_collected_file: Optional[CollectedFile],  # pylint: disable=unused-argument
    ) -> bool:
        """Check if the file should be processed"""
        return collected_file.original != collected_file.merged

    @classmethod
    def should_process_file(
        cls, collected_file: CollectedFile, base_collected_file: Optional[CollectedFile]
    ) -> bool:
        """
        Check if the file should be processed

        This is also usable by dapi servers to determine if a file should be processed.
        """
        if (
            base_collected_file
            and base_collected_file.filepath != collected_file.filepath
        ):
            raise ValueError(
                f"Base collected file filepath {base_collected_file.filepath} does not match "
                f"collected file filepath {collected_file.filepath}"
            )
        return cls._should_process_file(collected_file, base_collected_file)

    def write_files(self) -> Tuple[List[str], List[str]]:
        """Create or update the files"""
        written_files = []
        skipped_files = []
        for filepath, collected_file in self.collected_files.items():
            self.config.assert_dapi_location_is_valid(filepath)
            if self.always_write or self.should_process_file(
                collected_file, self.base_collected_files.get(collected_file.filepath)
            ):
                # Create the directory if it does not exist
                dir_name = os.path.dirname(filepath)
                os.makedirs(dir_name, exist_ok=True)

                written_files.append(filepath)
                with open(filepath, "w", encoding="utf-8") as file_handle:
                    jsonschema_ref = collected_file.merged.get("schema")
                    json_spec = fetch_schema(jsonschema_ref) if jsonschema_ref else None
                    sorted_yaml_dump(
                        collected_file.merged,
                        file_handle,
                        json_spec=json_spec,
                        yaml=self.yaml,
                    )
            else:
                skipped_files.append(filepath)
        return written_files, skipped_files
