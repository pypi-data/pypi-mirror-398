# pylint: disable=too-many-locals, too-many-function-args, duplicate-code
"""ActiveRecord DAPI validators."""

import copy
import functools
import os
import re
from dataclasses import dataclass
from typing import Dict, List
from typing import Optional as OptionalType
from typing import Set, Union

import sentry_sdk
from pyparsing import Dict as DictParser
from pyparsing import (
    Group,
    Literal,
    OneOrMore,
    Optional,
    QuotedString,
    Regex,
    Suppress,
    Word,
    ZeroOrMore,
    alphanums,
    nums,
)

from opendapi.adapters.file import find_files_with_suffix
from opendapi.config import (
    construct_dapi_source_sink_from_playbooks,
    construct_owner_team_urn_from_playbooks,
    construct_project_full_path,
    get_project_path_from_full_path,
)
from opendapi.models import ProjectConfig
from opendapi.validators.base import ValidationError
from opendapi.validators.dapi.base.main import DapiValidator, ORMIntegration
from opendapi.validators.dapi.models import ProjectInfo
from opendapi.validators.dapi.parsers.ddl import SqlDialect, parse_ddl


@dataclass
class SchemaRbColumn:
    """Data class for a column in a table in a rails project schema."""

    column_type: str
    column_name: str
    column_options: dict

    def for_dapi(self) -> dict:
        """Return the column as a dictionary for DAPI."""
        return {
            "name": self.column_name,
            "data_type": self.column_type,
            "is_nullable": not self.column_options.get("null") == "false",
        }


@dataclass
class SchemaRbIndex:
    """Data class for an index in a table in a rails project schema."""

    table_name: str
    index_columns: List[str]
    index_options: dict


@dataclass
class SchemaRbTable:  # pylint: disable=too-many-instance-attributes
    """Data class for a table in a rails project schema."""

    table_name: str
    table_options: dict
    parsed_columns: List[SchemaRbColumn]
    parsed_indices: List[SchemaRbIndex]

    @property
    def _table_options_primary_keys(self) -> List[str]:
        """Get the primary keys in the table options."""
        if isinstance(self.table_options.get("primary_key"), str):
            return [self.table_options.get("primary_key")]
        if getattr(self.table_options.get("primary_key"), "asList", None):
            return self.table_options["primary_key"].asList()
        return []

    @property
    def columns(self) -> List[SchemaRbColumn]:
        """Get the columns in the table."""
        id_option = self.table_options.get("id", "true")
        pk_col_name = None
        pk_col_type = None
        if primary_keys := self._table_options_primary_keys:
            if len(primary_keys) == 1:
                pk_col_name = primary_keys[0]
                pk_col_type = "bigint" if id_option in {"true", "false"} else id_option
            else:
                # for non-ID and composite primary keys,
                # columns must be explicitly listed
                pk_col_name = None
                pk_col_type = None
        elif id_option == "true":
            pk_col_name = "id"
            pk_col_type = "bigint"
        elif id_option != "false":
            pk_col_name = "id"
            pk_col_type = id_option
        else:
            pk_col_name = None
            pk_col_type = None

        columns_by_name = {col.column_name: col for col in self.parsed_columns}
        if pk_col_name in columns_by_name:
            columns_by_name[pk_col_name].column_options["primary_key"] = "true"
            columns_by_name[pk_col_name].column_options["null"] = "false"
        elif pk_col_name and pk_col_type:
            columns_by_name[pk_col_name] = SchemaRbColumn(
                pk_col_type,
                pk_col_name,
                {"null": "false", "primary_key": "true"},
            )

        return list(columns_by_name.values())

    @property
    def primary_keys(self) -> List[str]:
        """Get the primary keys in the table."""
        if table_option_primary_keys := self._table_options_primary_keys:
            return table_option_primary_keys

        # Case when the primary key is not specified in the table options
        columns_with_primary_key = []
        for column in self.columns:
            if column.column_options.get("primary_key") == "true":
                columns_with_primary_key.append(column.column_name)
        return columns_with_primary_key


@dataclass
class StructureSqlColumn:
    """Data class for a column in a table in a SQL schema."""

    column_name: str
    column_type: str
    is_nullable: bool

    def for_dapi(self) -> dict:
        """Return the column as a dictionary for DAPI."""
        return {
            "name": self.column_name,
            "data_type": self.column_type,
            "is_nullable": self.is_nullable,
        }


@dataclass
class StructuredSqlTable:
    """Data class for a table in a SQL schema."""

    table_name: str
    columns: List[StructureSqlColumn]
    primary_keys: List[str]


@dataclass
class ActiveRecordProjectInfo(ProjectInfo):
    """Data class for a rails project information"""

    # Required for SQL artifacts, not used for schema.rb artifacts
    dialect: OptionalType[SqlDialect] = None

    @property
    def project_name(self) -> str:
        """Get the name of the project."""
        # root is the project - so we set that to the project name
        if self.root_path.strip("/") == self.full_path.strip("/"):
            return os.path.basename(self.full_path)

        # if not, we use the relative project_path
        proj_path = get_project_path_from_full_path(self.root_path, self.full_path)
        return proj_path.strip("/").replace("/", ".")

    def is_sql_artifact(self) -> bool:
        """Check if the artifact is a SQL artifact."""
        return self.artifact_full_path.endswith(".sql")

    def construct_urn(self, table_name: str) -> str:
        """Construct the URN for the table."""
        return (
            f"{self.org_name_snakecase}.activerecord.{self.project_name}.{table_name}"
        )

    def construct_datastores(self, table_name: str) -> List[str]:
        """Construct the datastores for the table."""
        return DapiValidator.add_non_playbook_datastore_fields(
            construct_dapi_source_sink_from_playbooks(self.config.playbooks, table_name)
            if self.config.playbooks
            else {"sources": [], "sinks": []}
        )

    def construct_team_urn(self, table_name: str) -> OptionalType[str]:
        """Construct the team URN for the table."""
        return (
            construct_owner_team_urn_from_playbooks(
                self.config.playbooks, table_name, self.artifact_full_path
            )
            if self.config.playbooks
            else None
        )

    @functools.cached_property
    def missing_tables(self) -> Set[str]:
        """Get the expected number of tables in the schema."""
        with open(self.artifact_full_path, "r", encoding="utf-8") as file:
            total_table_names_in_file = set(
                re.findall(r'(?i)create_table\s+"([^"]+)"', file.read())
            )
            return total_table_names_in_file - {
                table.table_name for table in self.tables
            }

    @functools.cached_property
    def tables(self) -> List[Union[SchemaRbTable, StructuredSqlTable]]:
        """Get the tables in the schema."""
        if self.is_sql_artifact():
            return self.parse_sql_schema()

        return self.parse_rb_schema()

    def parse_sql_schema(self) -> List[StructuredSqlTable]:
        """Parse the structure.sql file."""
        with open(self.artifact_full_path, "r", encoding="utf-8") as file:
            ddl = file.read()

        ddl_tables = parse_ddl(ddl, self.dialect)
        tables = []
        for table in ddl_tables:
            tables.append(
                StructuredSqlTable(
                    table.fq_name,
                    [
                        StructureSqlColumn(
                            column.name,
                            column.type,
                            column.is_nullable,
                        )
                        for column in table.columns
                    ],
                    table.primary_key.columns if table.primary_key else [],
                )
            )
        return tables

    def parse_rb_schema(self) -> List[SchemaRbTable]:
        """Parse the schema.rb file."""
        # Define pyparsing elements
        integer_or_float = Word(nums + ".")
        boolean = Literal("true") | Literal("false")
        nil = Literal("nil")
        identifier = Word(alphanums + "_")
        quoted_string = QuotedString('"', escChar="\\")
        string_array = Group(
            Suppress("[")
            + ZeroOrMore(quoted_string + Optional(Suppress(",")))
            + Suppress("]")
        )
        empty_dict = Literal("{}")
        arrows = Literal("->") | Literal("=>")
        ruby_symbol = Suppress(":") + identifier
        comment_line = Suppress("#") + Regex(".*")
        non_matching_character = Regex(".{1,}")

        option_val_simple = (
            quoted_string
            | integer_or_float
            | boolean
            | string_array
            | ruby_symbol
            | nil
            | empty_dict
        )
        # t.primary_key "id", :uuid, default: { "gen_random_uuid()" }
        option_val_set = (
            Suppress("{")
            + OneOrMore(option_val_simple + Optional(Suppress(",")))
            + Suppress("}")
        )
        # t.primary_key "id", :uuid, default: -> { key1: "gen_random_uuid()" }
        # partition_by: {strategy: :list, key: ["computed_at"]}
        option_val_dict = DictParser(
            ZeroOrMore(
                Suppress("{")
                + OneOrMore(
                    Group(
                        identifier
                        + Suppress(":")
                        + Optional(Suppress(arrows))
                        + option_val_simple
                        + Optional(Suppress(","))
                    )
                )
                + Suppress("}")
            )
        )
        option_value = option_val_simple | option_val_set | option_val_dict
        options = DictParser(
            ZeroOrMore(
                Group(
                    identifier
                    + Suppress(":")
                    + Optional(Suppress(arrows))
                    + option_value
                    + Optional(Suppress(","))
                )
            )
        )

        # create_table "table_name", id: :uuid, primary_key: "custom_id", force: :cascade do |t|
        # create_table "table_name", id: :uuid, primary_key: "custom_id",
        # #            partition_by: {strategy: :list, key: ["computed_at"]}, force: :cascade do |t|
        table_start = Group(
            Suppress("create_table")
            + quoted_string("table_name")
            + Optional(Suppress(",") + options("table_options"))
            + Suppress("do")
            + Suppress("|t|")
        )

        # t.string "column_name", limit: 255, null: false
        column_parser = Group(
            Suppress("t.")
            + identifier("column_type")
            + quoted_string("column_name")
            + Optional(Suppress(","))
            + Optional(options("column_options"))
        )
        t_index_parser = Group(
            Suppress("t.index")
            + (quoted_string | string_array)("index_columns")
            + Optional(Suppress(","))
            + Optional(options("index_options"))
        )
        t_primary_key_parser = Group(
            Suppress("t.primary_key")
            + (quoted_string | string_array)("primary_key")
            + Optional(Suppress(","))
            + Optional(quoted_string | ruby_symbol)("primary_key_type")
            + Optional(Suppress(","))
            + Optional(options("primary_key_options"))
        )
        non_matching_column_parser = Suppress("t.") + non_matching_character
        columns_parser = ZeroOrMore(
            t_primary_key_parser
            | t_index_parser
            | column_parser
            | Suppress(comment_line)
            | Suppress(non_matching_column_parser)
        )

        # end
        table_end = Suppress("end")

        # ActiveRecord::Schema.define(version: 202202062227) do
        # ActiveRecord::Schema[7.1].define(version: 2024_01_10_212207) do
        rails_version = Suppress("[") + Word(alphanums + ".") + Suppress("]")
        version_parser = (
            Suppress("ActiveRecord::Schema")
            + Optional(rails_version)
            + Suppress(".define(version:")
            + integer_or_float("version")
            + Suppress(") do")
        )

        # Comment parser
        comments_parser = Group(comment_line)

        # Group the table elements
        tables_parser = Group(
            table_start("table_info") + columns_parser("columns") + table_end
        ).setResultsName("table")

        # add_index "table_name", ["column_name", "column_name"], name: "index_name"
        index_column = string_array | quoted_string
        add_indices_parser = Group(
            Suppress("add_index")
            + quoted_string("table_name")
            + Suppress(",")
            + index_column("index_columns")
            + Optional(Suppress(","))
            + Optional(options("index_options"))
        )

        # Combine the parsers
        full_parser = ZeroOrMore(
            version_parser
            | comments_parser
            | tables_parser
            | add_indices_parser
            | non_matching_character
        )("elements")

        # Parse the Ruby schema.rb content
        result = full_parser.parseFile(self.artifact_full_path)

        # Extract tables and indices separately
        tables = []
        for table in result["elements"]:
            if "table_info" in table:
                table_name = table["table_info"]["table_name"]
                table_options = table["table_info"]["table_options"]
                columns = {}
                # construct obvious columns
                for column in table["columns"]:
                    if "column_name" in column:
                        columns[column["column_name"]] = SchemaRbColumn(
                            column["column_type"],
                            column["column_name"],
                            column["column_options"],
                        )
                # Parse the t.primary_key and add the primary key to the columns
                for column in table["columns"]:
                    # Found t.primary_key - just update the table options accordingly
                    if "primary_key" in column:
                        table_options["primary_key"] = column["primary_key"]
                        table_options["id"] = column.get("primary_key_type", "bigint")
                        table_options["primary_key_options"] = column.get(
                            "primary_key_options", {}
                        )
                # Gather indices
                indices = []
                for index in result["elements"]:
                    if "index_columns" in index and str(index["table_name"]) == str(
                        table_name
                    ):
                        indices.append(
                            SchemaRbIndex(
                                str(index["table_name"]),
                                dict(index["index_columns"]),
                                dict(index["index_options"]),
                            )
                        )

                # Parse the t.index and add to indices
                for column in table["columns"]:
                    if "index_columns" in column:
                        indices.append(
                            SchemaRbIndex(
                                table_name,
                                dict(column["index_columns"]),
                                dict(column["index_options"]),
                            )
                        )

                tables.append(
                    SchemaRbTable(
                        str(table_name),
                        dict(table_options),
                        list(columns.values()),
                        indices,
                    )
                )
        return tables


class ActiveRecordDapiValidator(DapiValidator[ActiveRecordProjectInfo]):
    """
    Validator class for DAPI files created for Rails ActiveRecord.
    """

    INTEGRATION_NAME = ORMIntegration.ACTIVERECORD
    DEFAULT_ARTIFACT_PATH = "db/schema.rb"

    def get_all_projects(self) -> List[ActiveRecordProjectInfo]:
        """Generate a list of all projects that this validator should check"""

        schema_file_suffix = (
            f"/{self.integration_config.artifact_path or self.DEFAULT_ARTIFACT_PATH}"
        )
        all_schema_files = find_files_with_suffix(self.root_dir, [schema_file_suffix])

        projects = []
        for schema_file in all_schema_files:
            base_dir = schema_file.replace(schema_file_suffix, "")
            project_path = get_project_path_from_full_path(self.root_dir, base_dir)
            artifact_path = get_project_path_from_full_path(base_dir, schema_file)

            override = ProjectConfig(
                project_path=project_path,
                artifact_path=artifact_path,
                dialect=self.integration_config.dialect,
                include_models=self.integration_config.include_models,
            )

            projects.append(self.get_project(override))

        return projects

    def get_project(self, project_config: ProjectConfig) -> ActiveRecordProjectInfo:
        """Given a project config, return  object"""

        copy_project_config = copy.copy(project_config)
        project_full_path = construct_project_full_path(
            self.root_dir, copy_project_config.project_path
        )

        copy_project_config.artifact_path = (
            copy_project_config.artifact_path or f"{self.DEFAULT_ARTIFACT_PATH}"
        )

        copy_project_config.include_models = (
            copy_project_config.include_models or self.integration_config.include_models
        )

        dialect_value = copy_project_config.dialect or self.integration_config.dialect
        dialect = SqlDialect(dialect_value) if dialect_value else None

        return ActiveRecordProjectInfo(
            org_name_snakecase=self.config.org_name_snakecase,
            root_path=self.root_dir,
            config=copy_project_config,
            full_path=project_full_path,
            artifact_full_path=os.path.join(
                project_full_path, copy_project_config.artifact_path
            ),
            dialect=dialect,
        )

    def assert_dialect_for_sql_artifact(self, projects: List[ActiveRecordProjectInfo]):
        """Assert that the dialect is set for the SQL artifact"""
        errors = []

        for project in projects:
            if project.is_sql_artifact() and project.dialect is None:
                errors.append(
                    f"Dialect not found for project {project.full_path}. "
                    "Please specify the dialect in the project config."
                )
        if errors:
            raise ValidationError("\n".join(errors))

    def validate_projects(self, projects: List[ActiveRecordProjectInfo]):
        """Validate the projects"""
        self.assert_artifact_files_exist(projects)
        self.assert_dialect_for_sql_artifact(projects)

    def _get_base_generated_files(self) -> Dict[str, Dict]:
        result = {}
        for project in self.selected_projects():

            if project.missing_tables:
                sentry_sdk.capture_message(
                    "ActiveRecord parser returned incomplete results "
                    f"for commit {self.change_trigger_event.after_change_sha} "
                    f"of repo {self.change_trigger_event.repo_full_name} "
                    f"and project {project.full_path}: {', '.join(project.missing_tables)}"
                )

            for table in project.tables:
                if project.is_model_included(
                    table.table_name, project.artifact_full_path
                ):
                    dapi_location = project.construct_dapi_location(table.table_name)
                    generated_fields = [field.for_dapi() for field in table.columns]
                    dapi_urn = project.construct_urn(table.table_name)
                    result[dapi_location] = (
                        self.add_default_non_generated_schema_portions(
                            {
                                "urn": dapi_urn,
                                "owner_team_urn": project.construct_team_urn(
                                    table.table_name
                                ),
                                "datastores": project.construct_datastores(
                                    table.table_name
                                ),
                                "fields": generated_fields,
                                "primary_key": table.primary_keys,
                                "context": {
                                    "service": project.project_name,
                                    "integration": "activerecord",
                                    "rel_model_path": os.path.relpath(
                                        project.artifact_full_path,
                                        os.path.dirname(dapi_location),
                                    ),
                                },
                            }
                        )
                    )
        return result
