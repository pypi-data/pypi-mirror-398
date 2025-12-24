"""Constants and reusable definitions for the OpenDAPI Python client."""

from __future__ import annotations

from enum import Enum
from typing import List


class SqlDialect(Enum):
    """
    SQL Dialects
    Also used in parses.ddl - so check for completeness of support.
    """

    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRES = "postgres"


class ORMIntegration(Enum):
    """Enum for the ORM integration"""

    ACTIVERECORD = "activerecord"
    ALEMBIC = "alembic"
    DBT = "dbt"
    LIQUIBASE = "liquibase"
    PRISMA = "prisma"
    PYNAMODB = "pynamodb"
    SQLALCHEMY = "sqlalchemy"
    SEQUELIZE = "sequelize"
    TYPEORM = "typeorm"
    PROTOBUF = "protobuf"
    PYICEBERG = "pyiceberg"
    NO_ORM_FALLBACK = "no_orm_fallback"

    @classmethod
    def integrations(cls) -> List[ORMIntegration]:
        """Return the list of integrations"""
        return [
            integration for integration in cls if integration != cls.NO_ORM_FALLBACK
        ]


TEAMS_SUFFIX = [".teams.yaml", ".teams.yml", ".teams.json"]
DATASTORES_SUFFIX = [".datastores.yaml", ".datastores.yml", ".datastores.json"]
PURPOSES_SUFFIX = [".purposes.yaml", ".purposes.yml", ".purposes.json"]
DAPI_SUFFIX = [".dapi.yaml", ".dapi.yml", ".dapi.json"]
SUBJECTS_SUFFIX = [".subjects.yaml", ".subjects.yml", ".subjects.json"]
CATEGORIES_SUFFIX = [".categories.yaml", ".categories.yml", ".categories.json"]
OPENDAPI_CONFIG_SUFFIX = [
    "opendapi.config.yaml",
    "opendapi.config.yml",
    "opendapi.config.json",
]
GITHUB_ACTIONS_SUFFIX = [".github/workflows/opendapi_ci.yml"]

ALL_OPENDAPI_SUFFIXES = (
    TEAMS_SUFFIX
    + DATASTORES_SUFFIX
    + PURPOSES_SUFFIX
    + DAPI_SUFFIX
    + SUBJECTS_SUFFIX
    + CATEGORIES_SUFFIX
    + OPENDAPI_CONFIG_SUFFIX
    + GITHUB_ACTIONS_SUFFIX
)

OPENDAPI_DOMAIN = "opendapi.org"
OPENDAPI_URL = f"https://{OPENDAPI_DOMAIN}/"
OPENDAPI_SPEC_URL = OPENDAPI_URL + "spec/{version}/{entity}.json"

PLACEHOLDER_TEXT = "placeholder text"

CONFIG_FILEPATH_FROM_ROOT_DIR = "opendapi.config.yaml"
DEFAULT_DAPIS_DIR = "dapis"
GITHUB_ACTIONS_FILEPATH_FROM_ROOT_DIR = ".github/workflows/opendapi_ci.yml"
DEFAULT_DAPI_SERVER_HOSTNAME = "https://api.woven.dev"

REFS_PREFIXES = {
    r"^refs/heads/",
    r"refs/pull/\d+/",
}


class HTTPMethod(Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"


class IntegrationMode(Enum):
    """Enum for the integration mode"""

    ACTIVE = "active"
    OBSERVABILITY = "observability"


class OpenDAPIEntity(Enum):
    """The various opendapi entities"""

    CATEGORIES = "categories"
    DAPI = "dapi"
    DATASTORES = "datastores"
    PURPOSES = "purposes"
    SUBJECTS = "subjects"
    TEAMS = "teams"
    OPENDAPI_CONFIG = "opendapi_config"

    # legacy ones we need to remove after we are certain no
    # old PREs are in use
    SINGULAR_DATASTORE = "datastore"
    SINGULAR_PURPOSE = "purpose"
    SINGULAR_TEAM = "team"

    @classmethod
    def entities(cls):
        """Return the entities."""
        return [
            cls.CATEGORIES,
            cls.DAPI,
            cls.DATASTORES,
            cls.PURPOSES,
            cls.SUBJECTS,
            cls.TEAMS,
            cls.OPENDAPI_CONFIG,
        ]


class CommitType(Enum):
    """The various commit types"""

    BASE = "base"
    HEAD = "head"
    CURRENT = "current"


########### Schema Definitions ###########

DAPI_ORM_EXTRACTED_FIELDS_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$defs": {
        "field": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                },
                "data_type": {
                    "type": "string",
                },
                "is_nullable": {
                    "type": "boolean",
                },
                "enum_values": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
            "required": ["name", "data_type"],
        }
    },
    "type": "object",
    "properties": {
        "schema": {
            "type": "string",
            "format": "uri",
        },
        "urn": {
            "type": "string",
            "pattern": "^([\\w-]+\\.)+[\\w-]+$",
        },
        "fields": {
            "type": "array",
            "items": {"$ref": "#/$defs/field"},
            "minItems": 1,
        },
        "primary_key": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
    },
    "required": ["schema", "urn", "fields", "primary_key"],
}


# Essentially, things that must be gleaned from the client
# have to be here, since we cannot get them on the server side,
DAPI_CLIENT_REQUIRED_MINIMAL_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$defs": {
        "field": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                },
                "data_type": {
                    "type": "string",
                },
                "is_nullable": {
                    "type": "boolean",
                },
                "description": {
                    "type": ["string", "null"],
                },
                "enum_values": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
            "required": ["name", "data_type", "is_nullable", "description"],
        }
    },
    "type": "object",
    "properties": {
        "schema": {
            "type": "string",
            "format": "uri",
        },
        "urn": {
            "type": "string",
            "pattern": "^([\\w-]+\\.)+[\\w-]+$",
        },
        "description": {
            "type": ["string", "null"],
        },
        "fields": {
            "type": "array",
            "items": {"$ref": "#/$defs/field"},
            "minItems": 1,
        },
        "primary_key": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "type": {
            "type": "string",
            "enum": ["entity", "event"],
        },
        "context": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                },
                "integration": {
                    "type": "string",
                },
                "rel_model_path": {
                    "type": "string",
                },
                "rel_doc_path": {
                    "type": "string",
                },
            },
        },
    },
    "required": ["schema", "urn", "description", "fields", "primary_key", "type"],
}
