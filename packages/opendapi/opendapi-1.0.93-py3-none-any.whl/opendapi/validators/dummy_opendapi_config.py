"""Teams validator module"""

import functools
from typing import Dict

from opendapi.config import OpenDAPIConfig
from opendapi.defs import OPENDAPI_CONFIG_SUFFIX, OpenDAPIEntity
from opendapi.validators.base import BaseValidator


class DummyOpendapiConfigValidator(BaseValidator):
    """
    Validator class for Subjects files
    """

    SUFFIX = OPENDAPI_CONFIG_SUFFIX
    SPEC_VERSION = "0-0-1"
    ENTITY = OpenDAPIEntity.OPENDAPI_CONFIG

    # there should never be anything to merge since they are not allowed to differ
    STRICT_EQUALITY = True

    @functools.cached_property
    def original_file_state(self) -> Dict[str, Dict]:
        """Get the original file state"""
        # NOTE: the OpendapiConfig usually does some translation (i.e. for runtimes, etc)
        #       and so we need to make sure that this undergoes the same
        base_original_file_state = super().original_file_state
        return {
            filepath: OpenDAPIConfig.ensure_schema_add_backfills(content)
            for filepath, content in base_original_file_state.items()
        }

    @functools.cached_property
    def generated_file_state(self) -> Dict[str, Dict]:
        """Collect the raw generated file state"""
        # we never generate files for this validator, so it will always be the same as the original
        return self.original_file_state

    # NOTE: schema validation is already done in the base validator

    def _get_base_generated_files(self) -> Dict[str, Dict]:
        """Set Autoupdate templates in {file_path: content} format"""
        raise NotImplementedError(
            "DummyOpendapiConfigValidator does not generate files"
        )
