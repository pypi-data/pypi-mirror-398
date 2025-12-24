"""Models for use in opendapi functions."""

# pylint: disable=too-few-public-methods

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


def to_snake_case(
    entity_name: str,
    split_at_digits: bool = False,
) -> str:
    """
    Convert a string to snake case
    """
    # camelCase -> PascalCase
    entity_name = entity_name[0].upper() + entity_name[1:]
    # PascalCase -> snake_case
    snake_case = ""
    prev_wasnt_upper = False
    prev_was_digit_or_underscore = False
    for char in entity_name:
        if char.isupper():
            if prev_wasnt_upper:
                snake_case += "_"
            prev_wasnt_upper = False
        else:
            prev_wasnt_upper = True

        if split_at_digits:
            if char.isdigit():
                if not prev_was_digit_or_underscore:
                    snake_case += "_"
                prev_was_digit_or_underscore = True
            elif char == "_":
                prev_was_digit_or_underscore = True
            else:
                prev_was_digit_or_underscore = False

        snake_case += char.lower()
    return snake_case


def to_fivetran_snake_case(entity_name: str) -> str:
    """
    Convert a string to snake case
    """
    return to_snake_case(entity_name, split_at_digits=True)


def to_camel_case(entity_name: str) -> str:
    """
    Convert a string to camel case
    """
    snake_case = to_snake_case(entity_name)

    # snake_case -> camelCase
    camel_case = ""
    char_iter = iter(snake_case)
    char = next(char_iter)
    while char:
        if char == "_":
            char = next(char_iter, None)
            if char:
                camel_case += char.upper()
        else:
            camel_case += char
        char = next(char_iter, None)

    return camel_case


def to_pascal_case(entity_name: str) -> str:
    """
    Convert a string to pascal case
    """
    camel_case = to_camel_case(entity_name)
    return camel_case[0].upper() + camel_case[1:]


_TRANSFORM_TO_FUNCTION = {
    "pascal_case": to_pascal_case,
    "camel_case": to_camel_case,
    "snake_case": to_snake_case,
    "fivetran_snake_case": to_fivetran_snake_case,
}


class NameTransform(Enum):
    """
    Name transform
    """

    PASCAL_CASE = "pascal_case"
    CAMEL_CASE = "camel_case"
    SNAKE_CASE = "snake_case"
    FIVETRAN_SNAKE_CASE = "fivetran_snake_case"

    def transform(self, entity_name: str) -> str:
        """
        Transform the entity name
        """
        return _TRANSFORM_TO_FUNCTION[self.value](entity_name)

    @staticmethod
    def apply(name_transform: NameTransform | None, entity_name: str) -> str:
        """
        Apply the name transform to the entity name
        """
        return name_transform.transform(entity_name) if name_transform else entity_name


class ConfigParam(Enum):
    """Enum for various configuration objects"""

    PROJECTS = "projects"
    PROJECT_PATH = "project_path"
    INCLUDE_ALL = "include_all"
    DIALECT = "dialect"
    INCLUDE_PROJECTS = "include_projects"
    INCLUDE_MODELS = "include_models"
    OVERRIDES = "overrides"
    PLAYBOOKS = "playbooks"
    # KBTODO deprecate:model_allowlist: as part of playbooks revamp
    MODEL_ALLOWLIST = "model_allowlist"
    ARTIFACT_PATH = "artifact_path"


class BaseConfig:
    """Base class for configuration objects"""

    @classmethod
    def from_dict(cls, data: dict):
        """Helper function to create a class using only necessary elements from the dict"""
        parameters = inspect.signature(cls).parameters
        filtered_data = {k: v for k, v in data.items() if k in parameters}
        return cls(**filtered_data)


@dataclass
class PlaybookConfig(BaseConfig):
    """Data class for a playbook item"""

    type: str
    datastore_urn: Optional[str] = None
    namespace: Optional[str] = None
    identifier_prefix: Optional[str] = None
    name_transform: Optional[NameTransform] = None
    team_urn: Optional[str] = None
    # KBTODO deprecate:model_allowlist: as part of playbooks revamp
    model_allowlist: Optional[List[str]] = field(default_factory=list)

    def __post_init__(self):
        """Post init"""
        # sorta hate this since wouldnt work if the dataclass was frozen,
        # but we can just swap from using a dataclass at that time...
        if self.name_transform:
            self.name_transform = NameTransform(self.name_transform)


@dataclass
class ProjectConfig(BaseConfig):
    """Data class for Project config"""

    # Project path relative to the repo
    project_path: str

    # Some applications / integrations have a schema file that needs to be handled
    artifact_path: Optional[str] = None
    include_models: Optional[List[str]] = field(default_factory=list)

    dialect: Optional[str] = None

    # KBTODO deprecate:model_allowlist: as part of playbooks revamp
    model_allowlist: Optional[List] = field(default_factory=list)
    playbooks: Optional[List[PlaybookConfig]] = field(default_factory=list)


@dataclass
class IntegrationConfig(BaseConfig):
    """Data class for a project item"""

    include_all: Optional[bool] = False
    include_projects: Optional[List[str]] = field(default_factory=list)
    include_models: Optional[List[str]] = field(default_factory=list)
    artifact_path: Optional[str] = None
    dialect: Optional[str] = None
    overrides: Optional[List[ProjectConfig]] = field(default_factory=list)
