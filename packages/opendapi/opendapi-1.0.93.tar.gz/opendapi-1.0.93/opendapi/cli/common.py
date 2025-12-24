"""Common utilities for the OpenDAPI CLI."""

import functools
import json
import os
from dataclasses import dataclass, fields
from typing import List, Optional, Protocol, Type, Union

import click
from jsonschema.exceptions import SchemaError
from jsonschema.validators import validator_for

from opendapi.config import OpenDAPIConfig
from opendapi.defs import CONFIG_FILEPATH_FROM_ROOT_DIR, OpenDAPIEntity
from opendapi.logging import logger


class BaseValidatorWithSuffix(Protocol):  # pylint: disable=too-few-public-methods
    """
    Protocol for all Validators with an ENTITY.

    Added to not include a circular import with BaseValidator.
    """

    ENTITY: OpenDAPIEntity


@dataclass(frozen=True)
class Schemas:
    """
    Schemas for various OpenDAPI entities.
    """

    # NOTE: this is done to make it hashable, since storing the dicts
    #       directly in the dataclass would make it unhashable
    teams_schema_str: Optional[str] = None
    datastores_schema_str: Optional[str] = None
    purposes_schema_str: Optional[str] = None
    dapi_schema_str: Optional[str] = None
    subjects_schema_str: Optional[str] = None
    categories_schema_str: Optional[str] = None
    opendapi_config_schema_str: Optional[str] = None

    @classmethod
    def create(
        cls,
        teams: Optional[dict] = None,
        datastores: Optional[dict] = None,
        purposes: Optional[dict] = None,
        dapi: Optional[dict] = None,
        subjects: Optional[dict] = None,
        categories: Optional[dict] = None,
        opendapi_config: Optional[dict] = None,
    ):
        """
        This method is used to create a Schemas object from the schemas.
        """
        return cls(
            teams_schema_str=json.dumps(teams) if teams else None,
            datastores_schema_str=json.dumps(datastores) if datastores else None,
            purposes_schema_str=json.dumps(purposes) if purposes else None,
            dapi_schema_str=json.dumps(dapi) if dapi else None,
            subjects_schema_str=json.dumps(subjects) if subjects else None,
            categories_schema_str=json.dumps(categories) if categories else None,
            opendapi_config_schema_str=(
                json.dumps(opendapi_config) if opendapi_config else None
            ),
        )

    @functools.cached_property
    def teams(self) -> Optional[dict]:
        """Return the teams schema."""
        return json.loads(self.teams_schema_str) if self.teams_schema_str else None

    @functools.cached_property
    def datastores(self) -> Optional[dict]:
        """Return the datastores schema."""
        return (
            json.loads(self.datastores_schema_str)
            if self.datastores_schema_str
            else None
        )

    @functools.cached_property
    def purposes(self) -> Optional[dict]:
        """Return the purposes schema."""
        return (
            json.loads(self.purposes_schema_str) if self.purposes_schema_str else None
        )

    @functools.cached_property
    def dapi(self) -> Optional[dict]:
        """Return the dapi schema."""
        return json.loads(self.dapi_schema_str) if self.dapi_schema_str else None

    @functools.cached_property
    def subjects(self) -> Optional[dict]:
        """Return the subjects schema."""
        return (
            json.loads(self.subjects_schema_str) if self.subjects_schema_str else None
        )

    @functools.cached_property
    def categories(self) -> Optional[dict]:
        """Return the categories schema."""
        return (
            json.loads(self.categories_schema_str)
            if self.categories_schema_str
            else None
        )

    @functools.cached_property
    def opendapi_config(self) -> Optional[dict]:
        """Return the opendapi config schema."""
        return (
            json.loads(self.opendapi_config_schema_str)
            if self.opendapi_config_schema_str
            else None
        )

    def __post_init__(self):
        """Validate the schemas."""
        self.validate_schemas()

    def validate_schemas(self):
        """Validate the schemas against their meta schema."""
        errors = []
        for field in fields(self):
            schema_name = field.name.replace("_schema_str", "")
            schema = getattr(self, schema_name)
            if schema:
                validator_cls = validator_for(schema)
                try:
                    validator_cls.check_schema(schema)
                except SchemaError as exc:
                    errors.append(f"Schema for {schema_name} is invalid: {exc}")
        if errors:
            print_cli_output(
                "OpenDAPI: Encountered validation errors",
                color="red",
                bold=True,
            )
            for error in errors:
                print_cli_output(error, color="red", bold=True)
            raise TypeError("\n".join(errors))

    def minimal_schema_for(
        self,
        validator_cls: Union[BaseValidatorWithSuffix, Type[BaseValidatorWithSuffix]],
    ) -> Optional[dict]:
        """Get the minimal schema for the given validator class."""
        if not hasattr(validator_cls, "SUFFIX"):
            raise ValueError(f"Unknown validator class: {validator_cls}")

        if validator_cls.ENTITY is OpenDAPIEntity.TEAMS:
            return self.teams
        if validator_cls.ENTITY is OpenDAPIEntity.DATASTORES:
            return self.datastores
        if validator_cls.ENTITY is OpenDAPIEntity.PURPOSES:
            return self.purposes
        if validator_cls.ENTITY is OpenDAPIEntity.DAPI:
            return self.dapi
        if validator_cls.ENTITY is OpenDAPIEntity.SUBJECTS:
            return self.subjects
        if validator_cls.ENTITY is OpenDAPIEntity.CATEGORIES:
            return self.categories
        if validator_cls.ENTITY is OpenDAPIEntity.OPENDAPI_CONFIG:
            return self.opendapi_config

        raise ValueError(f"Unknown validator class: {validator_cls}")


def check_command_invocation_in_root():
    """Check if the `opendapi` CLI command is invoked from the root of the repository."""
    if not (os.path.isdir(".github") or os.path.isdir(".git")):
        print_cli_output(
            "  This command must be run from the root of your repository. Exiting...",
            color="red",
        )
        raise click.Abort()
    print_cli_output(
        "  We are in the root of the repository. Proceeding...",
        color="green",
    )
    return True


def get_root_dir_validated() -> str:
    """Get the root directory of the repository."""
    root_dir = os.getcwd()
    check_command_invocation_in_root()
    return root_dir


def get_opendapi_config_from_root(
    local_spec_path: Optional[str] = None,
    validate_config: bool = False,
) -> OpenDAPIConfig:
    """Get the OpenDAPI configuration object."""
    root_dir = get_root_dir_validated()

    try:
        config = OpenDAPIConfig(root_dir, local_spec_path=local_spec_path)
        print_cli_output(
            f"  Found the {CONFIG_FILEPATH_FROM_ROOT_DIR} file. Proceeding...",
            color="green",
        )
        if validate_config:
            check_if_opendapi_config_is_valid(config)
        return config

    except FileNotFoundError as exc:
        print_cli_output(
            f"  The {CONFIG_FILEPATH_FROM_ROOT_DIR} file does not exist. "
            "Please run `opendapi init` first. Exiting...",
            color="red",
        )
        raise click.Abort() from exc


def load_opendapi_config(
    serialized_config: str,
    local_spec_path: Optional[str] = None,
    validate_config: bool = False,
) -> OpenDAPIConfig:
    """Get the OpenDAPI configuration object."""

    root_dir = get_root_dir_validated()

    config = OpenDAPIConfig(
        root_dir, local_spec_path=local_spec_path, serialized_config=serialized_config
    )
    print_cli_output(
        " Loaded the opendapi config. Proceeding...",
        color="green",
    )
    if validate_config:
        check_if_opendapi_config_is_valid(config)
    return config


def check_if_opendapi_config_is_valid(config: OpenDAPIConfig) -> bool:
    """Check if the `opendapi.config.yaml` file is valid."""
    try:
        config.validate()
    except Exception as exc:
        print_cli_output(
            f"  The `{CONFIG_FILEPATH_FROM_ROOT_DIR}` file is not valid. "
            f"`opendapi init` may rectify. {exc}. Exiting...",
            color="red",
        )
        raise click.Abort()
    print_cli_output(
        f"  The {CONFIG_FILEPATH_FROM_ROOT_DIR} file is valid. Proceeding...",
        color="green",
    )
    return True


def pretty_print_errors(errors: List[Exception]):
    """Prints all the errors"""
    if errors:
        print_cli_output(
            "OpenDAPI: Encountered validation errors",
            color="red",
            bold=True,
        )
    for error in errors:
        print_cli_output(
            f"OpenDAPI: {error.prefix_message}",
            color="red",
            bold=True,
        )
        for err in error.errors:
            print_cli_output(err)


def highlight_message(message: str):
    """Highlights the message"""
    return f"\n{'>' * 30}\n\n{message}\n\n{'>' * 30}\n"


def print_cli_output(
    message: str,
    color: str = "green",
    bold: bool = False,
    markdown_file: Optional[str] = None,
    no_text: bool = False,
    no_markdown: bool = False,
):
    """Print errors."""
    # Text message
    if not no_text:
        click.secho(message, fg=color, bold=bold)
        # LOG_LEVEL will be set to info only in non-test CI environments
        # The interactive CLI will only show errors
        logger.info(message)

    # Markdown message
    if markdown_file and not no_markdown:  # pragma: no cover
        with open(
            markdown_file,
            "a",
            encoding="utf-8",
        ) as m_file:
            print(f"{message}\n\n", file=m_file)
