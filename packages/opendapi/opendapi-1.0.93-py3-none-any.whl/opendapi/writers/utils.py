"""Writer utils"""

from typing import Type

from opendapi.defs import OpenDAPIEntity
from opendapi.writers.base import BaseFileWriter
from opendapi.writers.dapi import DapiFileWriter

ENTITY_TO_WRITER = {
    OpenDAPIEntity.DAPI: DapiFileWriter,
}


def get_writer_for_entity(entity: OpenDAPIEntity) -> Type[BaseFileWriter]:
    """Get the writer for the entity"""
    return ENTITY_TO_WRITER.get(entity, BaseFileWriter)
