"""
Utils relating to validators
"""

from typing import Callable, Dict, Type

from opendapi.defs import OpenDAPIEntity

from .base import BaseValidator
from .categories import CategoriesValidator
from .dapi import BaseDapiValidator
from .datastores import DatastoresValidator
from .dummy_opendapi_config import DummyOpendapiConfigValidator
from .purposes import PurposesValidator
from .subjects import SubjectsValidator
from .teams import TeamsValidator

_ENTITY_TO_VALIDATOR: Dict[OpenDAPIEntity, Type[BaseValidator]] = {
    OpenDAPIEntity.CATEGORIES: CategoriesValidator,
    OpenDAPIEntity.DAPI: BaseDapiValidator,
    OpenDAPIEntity.DATASTORES: DatastoresValidator,
    OpenDAPIEntity.PURPOSES: PurposesValidator,
    OpenDAPIEntity.SUBJECTS: SubjectsValidator,
    OpenDAPIEntity.TEAMS: TeamsValidator,
    OpenDAPIEntity.OPENDAPI_CONFIG: DummyOpendapiConfigValidator,
}


def get_merger_for_entity(
    entity: OpenDAPIEntity,
) -> Callable[[dict, dict], dict]:
    """Get the merger for the given entity."""
    return _ENTITY_TO_VALIDATOR[entity].merge
