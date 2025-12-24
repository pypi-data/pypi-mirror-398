"""dapi validator for prisma schemas"""

# pylint: disable=too-many-locals, too-many-instance-attributes, too-few-public-methods, R0801, too-many-statements

import copy
import os
from dataclasses import dataclass
from typing import Dict, List
from typing import Optional as OptionalType

from pyparsing import (
    Group,
    Keyword,
    OneOrMore,
    Optional,
    SkipTo,
    Suppress,
    Word,
    ZeroOrMore,
    alphanums,
    delimitedList,
    identbodychars,
    identchars,
    nestedExpr,
    nums,
    quoted_string,
    remove_quotes,
    restOfLine,
)

from opendapi.adapters.file import find_files_with_suffix
from opendapi.config import (
    construct_dapi_source_sink_from_playbooks,
    construct_owner_team_urn_from_playbooks,
    construct_project_full_path,
    get_project_path_from_full_path,
)
from opendapi.models import PlaybookConfig, ProjectConfig
from opendapi.validators.dapi.base.main import DapiValidator, ORMIntegration
from opendapi.validators.dapi.models import ProjectInfo


@dataclass
class Column:
    """Data class for a prisma column definition"""

    name: str
    data_type: str
    options: dict
    is_enum: bool = False

    def _prisma_type_to_dapi_datatype(self, prisma_type: str) -> str:
        """Convert the Prisma data type to DAPI data type"""
        if self.is_enum:
            return f"enum:{prisma_type}"
        return prisma_type.lower()

    def for_dapi(self) -> dict:
        """Return the column as a dictionary for DAPI."""
        return {
            "name": self.options.get("db_field") or self.name,
            "data_type": self._prisma_type_to_dapi_datatype(self.data_type),
            "is_nullable": self.options.get("nullable", False),
        }


@dataclass
class Table:
    """Data class for a prisma table definition"""

    table_name: str
    table_options: dict
    primary_keys: List[str]
    parsed_columns: List["Column"]
    parsed_indices: List["Index"]
    project_full_path: str
    schema_full_path: str
    org_name_snakecase: str
    playbooks: OptionalType[List[PlaybookConfig]] = None
    is_allowlisted: OptionalType[bool] = None

    def construct_urn(self) -> str:
        """Construct the URN for the table."""
        return f"{self.org_name_snakecase}.prisma.{self.project_name}.{self.table_name}"

    def construct_datastores(self) -> List[str]:
        """Get the datastores for the table."""
        return DapiValidator.add_non_playbook_datastore_fields(
            construct_dapi_source_sink_from_playbooks(self.playbooks, self.table_name)
            if self.playbooks
            else {"sources": [], "sinks": []}
        )

    def construct_team_urn(self) -> OptionalType[str]:
        """Construct the team URN for the table."""
        return (
            construct_owner_team_urn_from_playbooks(
                self.playbooks, self.table_name, self.schema_full_path
            )
            if self.playbooks
            else None
        )

    @property
    def columns(self) -> List[Column]:
        """Get the columns in the table."""
        return self.parsed_columns

    @property
    def project_name(self) -> str:
        """Get the name of the project"""
        path_split = os.path.split(self.project_full_path)
        project_path = (
            path_split[0] if path_split[1] == "prisma" else self.project_full_path
        )
        return (
            os.path.basename(project_path).replace("-", "_").replace(" ", "_").lower()
        )


@dataclass
class PrismaProjectInfo(ProjectInfo):
    """Data class for a prisma project information"""

    @property
    def tables(self) -> List["Table"]:
        """Returns a list of tables in the schema"""

        with open(self.artifact_full_path, encoding="utf-8") as schema_file:
            schema = schema_file.read()

        LBRACE, RBRACE, AT = map(Suppress, "{}@")  # pylint: disable=invalid-name
        identifier = Word(identchars, identbodychars)
        qtd_string = quoted_string().setParseAction(remove_quotes)

        # Define an enum and try to find all the enums in the input schema
        enum_defs = {}
        enums_pattern = (
            Suppress("enum")
            + identifier("name")
            + LBRACE
            + OneOrMore(Word(identchars))("enum_values")
            + RBRACE
        )

        for enum_def in enums_pattern.searchString(schema):
            enum_defs[enum_def.name] = list(enum_def.enum_values)

        # We will define a basic model pattern to COUNT the number of models in the schema
        # We will then use this to validate that all models were generated
        model_count_pattern = (
            Suppress("model")
            + identifier("table_name")
            + LBRACE
            + SkipTo(RBRACE)
            + RBRACE
        )

        expected_models = set(
            table.table_name for table in model_count_pattern.searchString(schema)
        )

        # Define the various datatypes
        integer = Keyword("Int")
        boolean = Keyword("Boolean")
        datetime = Keyword("DateTime")
        string = Keyword("String")
        unsupported = Keyword("Unsupported") + nestedExpr(ignore_expr=quoted_string())
        # Define a numeric literal pattern
        numeric_literal = Word(nums + ".")

        # Define a field type
        field_type = integer | datetime | string | boolean | unsupported | identifier

        # Define various keywords
        comment = Suppress(Group(Suppress("//") + restOfLine))

        # Define common patterns for decorators
        name_option = Optional(Suppress(Keyword("name")) + Suppress(":")) + qtd_string(
            "name_value"
        )
        map_option = Suppress(Keyword("map")) + Suppress(":") + qtd_string("map_value")
        field_length_option = (
            Keyword("length") + Suppress(":") + Word(nums)("length_value")
        )

        # A primary key is defined as @id
        id_attribute = Group(AT + Keyword("id"))("is_primary_key")

        # A compound id is defined as @@id([field1, field2, ...])
        compound_id = Group(
            Keyword("@@id")
            + Suppress("([")
            + delimitedList(
                identifier
                + Optional(
                    Suppress("(") + Suppress(field_length_option) + Suppress(")")
                )
            )("identifiers")
            + Suppress("]")
            + Optional(
                Suppress(",")
                + Suppress(delimitedList(name_option | map_option, delim=","))
            )
            + Suppress(")")
        )("compound_id")

        # Unique field is defined as @unique or @@unique([field1, field2, ...])
        # or @@unique([field1, field2(length: 10), ...], name: "constraint_name", map: "db_name")
        unique = Group(
            Keyword("@unique")
            + Optional(
                Suppress("(")
                + Suppress(delimitedList(name_option | map_option, delim=","))
                + Suppress(")")
            )
        )("is_unique")
        compound_unique = Group(
            Keyword("@@unique")
            + Suppress("([")
            + delimitedList(
                identifier
                + Optional(
                    Suppress("(") + Suppress(field_length_option) + Suppress(")")
                )
            )
            + Suppress("]")
            + Optional(
                Suppress(",")
                + Suppress(delimitedList(name_option | map_option, delim=","))
            )
            + Suppress(")")
        )("compound_unique")

        # A @@map definition is use to map a model definition to a different table name
        table_mapping = Group(
            Keyword("@@map") + Suppress("(") + name_option + Suppress(")")
        )("table_map")

        # A @@schema definition is used to define the schema for a table
        schema_mapping = Group(
            Keyword("@@schema") + Suppress("(") + name_option + Suppress(")")
        )("schema_map")

        # Map fields are used to map a model definition to an underlying database field
        map_attribute = Group(
            AT + Keyword("map") + Suppress("(") + name_option + Suppress(")")
        )("field_db_map")

        # Default value definition
        default = Group(
            AT
            + Suppress(Keyword("default"))
            + nestedExpr(ignore_expr=quoted_string() | numeric_literal)("value")
        )("default")

        index = Suppress(Group(Keyword("@@index") + restOfLine))

        generic_decorators = Suppress(
            AT
            + Word(alphanums + ".")
            + Optional(nestedExpr(ignore_expr=quoted_string() | numeric_literal))
        )

        # Ignore field definition
        ignore_attribute = Group(AT + Keyword("ignore"))("is_ignored")

        decorators = Group(
            ZeroOrMore(
                default
                | id_attribute
                | unique
                | map_attribute
                | ignore_attribute
                | generic_decorators
            )
        )
        relationship = Suppress(
            Group(
                identifier("field")
                + identifier("model")
                + Optional("?")("nullable")
                + Optional("[]")("is_array")
                + AT
                + Keyword("relation")
                + restOfLine
            )
        )

        # A field is defined as
        # field_name field_type @default(value) @id @unique  // comment
        field = Group(
            identifier("name")
            + field_type("type")
            + Optional("?")("nullable")
            + Optional("[]")("is_array")
            + decorators("info")
            + Optional(comment)
        )("field")

        # Ignore model definition
        ignore_model = Group(Keyword("@@ignore"))("is_ignored")

        # A table is defined as
        # model table_name {
        #   field1 field_type @default(value) @id @unique  // comment
        #   field2 field_type @default(value) @id @unique  // comment
        #   ...
        #   @@id([field1, field2, ...])
        #   @@unique([field1, field2, ...])
        #   @@index([field1, field2, ...])
        # }
        models = (
            Suppress("model")
            + identifier("table_name")
            + LBRACE
            + Group(
                OneOrMore(
                    relationship
                    | field
                    | comment
                    | compound_id
                    | compound_unique
                    | index
                    | ignore_model
                    | table_mapping
                    | schema_mapping
                )
            )("info")
            + RBRACE
        )

        tables = []
        parsed_models = set()
        ignored_models = set()
        for table in models.searchString(schema):
            if table.info.is_ignored:
                ignored_models.add(table.table_name)
                continue

            primary_keys = []
            columns = []
            table_name = table.table_name
            schema_name = None
            parsed_models.add(table_name)
            field_map = {}

            for row in table.info:
                if row.name and not row.info.is_ignored:
                    # This is a parsed column
                    column = row
                    default_value = (
                        column.info.default.value.as_list()[0]
                        if column.info.default
                        else None
                    )
                    db_field = (
                        column.info.field_db_map.name_value
                        if "field_db_map" in column.info
                        else column.name
                    )
                    field_map[column.name] = db_field
                    data_type = column.type[0]

                    columns.append(
                        Column(
                            name=column.name,
                            data_type=data_type,
                            is_enum=data_type in enum_defs,
                            options={
                                "nullable": bool(column.nullable),
                                "is_array": bool(column.is_array),
                                "default_value": default_value,
                                "db_field": db_field,
                            },
                        )
                    )

                    if column.info.is_primary_key:
                        primary_keys.append(column.name)

                elif row[0] == "@@id":
                    # This is a parsed compound primary key
                    primary_keys = row.identifiers.as_list()

                elif row[0] == "@@map":
                    # Remove the quotes and store the table name
                    table_name = row.name_value

                elif row[0] == "@@schema":
                    schema_name = row.name_value

            primary_keys = [field_map[pk] for pk in primary_keys]

            tables.append(
                Table(
                    table_name=table.table_name,
                    table_options={
                        "enum_defs": enum_defs,
                        "table_name": table_name,
                        "schema_name": schema_name,
                    },
                    primary_keys=primary_keys,
                    parsed_columns=columns,
                    parsed_indices=[],
                    project_full_path=self.full_path,
                    schema_full_path=self.artifact_full_path,
                    org_name_snakecase=self.org_name_snakecase,
                    playbooks=self.config.playbooks,
                    is_allowlisted=self.is_model_included(
                        table.table_name,
                        self.artifact_full_path,
                    ),
                )
            )

        missed_models = expected_models - parsed_models - ignored_models
        if missed_models:
            raise RuntimeError(
                f"Missed parsing the following models: {', '.join(missed_models)} "
                + f"from {self.artifact_full_path}"
            )
        return tables


class PrismaDapiValidator(DapiValidator[PrismaProjectInfo]):
    """
    Validator class for DAPI files created for Prisma schemas
    """

    INTEGRATION_NAME = ORMIntegration.PRISMA

    DEFAULT_ARTIFACT_PATH = ".prisma"
    # This is used by the npm prisma-multischema package. We will exclude the
    # subschemas directory from the search and parse only the combined schema file.
    EXCLUDE_DIRS_FOR_AUTODISCOVERY = ["subschemas"]

    def get_project(self, project_config: ProjectConfig) -> PrismaProjectInfo:
        """Given a project config, return ProjectInfo object"""

        copy_project_config = copy.deepcopy(project_config)
        project_full_path = construct_project_full_path(
            self.root_dir, copy_project_config.project_path
        )

        copy_project_config.artifact_path = (
            copy_project_config.artifact_path
            or self.integration_config.artifact_path
            or f"schema.{self.DEFAULT_ARTIFACT_PATH}"
        )
        copy_project_config.include_models = (
            copy_project_config.include_models or self.integration_config.include_models
        )

        return PrismaProjectInfo(
            org_name_snakecase=self.config.org_name_snakecase,
            root_path=self.root_dir,
            config=copy_project_config,
            full_path=project_full_path,
            artifact_full_path=os.path.join(
                project_full_path, copy_project_config.artifact_path
            ),
        )

    def get_all_projects(self) -> List[PrismaProjectInfo]:
        """Get projects from all prisma schema files."""

        all_schema_files = find_files_with_suffix(
            self.root_dir,
            [self.integration_config.artifact_path or f"{self.DEFAULT_ARTIFACT_PATH}"],
            exclude_dirs=self.EXCLUDE_DIRS_FOR_AUTODISCOVERY,
        )

        projects = []
        for schema_file in all_schema_files:
            schema_path = os.path.dirname(schema_file)
            artifact_path = os.path.basename(schema_file)

            if schema_path.endswith("/prisma"):
                schema_path = os.path.dirname(schema_path)
                artifact_path = os.path.join("prisma", artifact_path)

            project_path = get_project_path_from_full_path(self.root_dir, schema_path)

            config = ProjectConfig(
                project_path=project_path,
                artifact_path=artifact_path,
                include_models=self.integration_config.include_models,
            )
            projects.append(self.get_project(config))

        return projects

    def validate_projects(self, projects: List[PrismaProjectInfo]):
        """Verify that all projects and their schema files exist"""
        self.assert_artifact_files_exist(projects)

    def _get_base_generated_files(self) -> Dict[str, Dict]:
        result = {}
        for project in self.selected_projects():
            for table in project.tables:
                if table.is_allowlisted:
                    dapi_location = project.construct_dapi_location(table.table_name)
                    result[dapi_location] = (
                        self.add_default_non_generated_schema_portions(
                            {
                                "urn": table.construct_urn(),
                                "owner_team_urn": table.construct_team_urn(),
                                "datastores": table.construct_datastores(),
                                "fields": [field.for_dapi() for field in table.columns],
                                "primary_key": table.primary_keys,
                                "context": {
                                    "service": table.project_name,
                                    "integration": "prisma",
                                    "rel_model_path": os.path.relpath(
                                        project.artifact_full_path,
                                        os.path.dirname(dapi_location),
                                    ),
                                },
                            }
                        )
                    )
        return result


if __name__ == "__main__":  # pragma: no cover
    import sys
    from pprint import pprint

    proj_cfg = ProjectConfig(project_path="test_app")

    pprint(
        PrismaProjectInfo(
            config=proj_cfg,
            full_path=None,
            root_path="test_root",
            artifact_full_path=sys.argv[1],
            org_name_snakecase="test_org",
        ).tables,
        sort_dicts=True,
    )
