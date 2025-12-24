# pylint: disable=pointless-statement,expression-not-assigned,too-many-statements
"""TypeORM (TypeScript) DAPI validator module"""

import os
from dataclasses import asdict, dataclass
from functools import cached_property
from typing import Any
from typing import Dict as DictType
from typing import List
from typing import Optional as OptionalType
from typing import Tuple

from pyparsing import (
    DelimitedList,
    Dict,
    Forward,
    Group,
    Keyword,
    LineEnd,
    OneOrMore,
    Optional,
    ParserElement,
    ParseResults,
    QuotedString,
    Suppress,
    Word,
    ZeroOrMore,
    alphas,
    cpp_style_comment,
    nested_expr,
    pyparsing_common,
    replaceWith,
)

from opendapi.config import (
    construct_dapi_source_sink_from_playbooks,
    construct_owner_team_urn_from_playbooks,
)
from opendapi.validators.dapi.base.js import JsProjectsDapiValidatorBase
from opendapi.validators.dapi.base.main import ORMIntegration
from opendapi.validators.dapi.models import PackageScopedProjectInfo

# Memoize the parser element to improve performance
ParserElement.enablePackrat()  # pylint: disable=no-value-for-parameter


@dataclass
class Module:
    """Data class for modules in a TypeORM model"""

    imports: ParseResults
    filename: str

    @property
    def module_name(self) -> str:
        """Get the module name"""
        return self.filename.replace(".ts", "")

    def get_import_info(self, base_class: str) -> DictType[str, OptionalType[str]]:
        """Get the base class of the table and its file path"""
        result = {
            "class": base_class,
            "alias": base_class,
            # default to the current file assuming the base class is in the same file
            "module_name": self.filename,
        }

        # check if the base class is imported
        for import_statement in self.imports:
            absolute_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(self.filename), import_statement["import_from"]
                )
            )
            for import_name in import_statement["import_names"]:
                if " as " in import_name:
                    imported_name, alias = import_name.strip().split(" as ")
                else:
                    # import names may have trailing spaces
                    imported_name, alias = import_name.strip(), import_name.strip()

                if alias == base_class:
                    result["class"] = imported_name
                    result["module_name"] = absolute_path
                    return result

        return result


@dataclass
class Column:
    """Data class for a column in a TypeORM model"""

    prop: ParseResults
    column_decorators: List[ParseResults]
    module: Module
    relation_decorator: OptionalType[ParseResults] = None

    def get_name(self) -> Tuple[str, bool]:
        """Get column name and whether the name was explicitly defined"""
        # No need to look beyond the first decorator because the name is guaranteed to be the same
        decorator_args = self.column_decorators[0]["decorator_args"]

        # Look for name in column options
        for arg in decorator_args:
            if isinstance(arg, ParseResults) and "name" in arg:
                return arg["name"], True

        # Fall back to property name
        return self.prop["property_name"], False

    @property
    def name(self) -> str:
        """Get column name"""
        return self.get_name()[0]

    @property
    def embedded_entity(self) -> OptionalType[DictType[str, OptionalType[str]]]:
        """Get the embedded entity that the column references"""
        for decorator in self.column_decorators:
            if (
                decorator["decorator_name"] == "Column"
                and "lambda_function" in decorator
            ):
                # @Column(() => Name) is how these are defined
                class_name = decorator["lambda_function"][-1]
                import_info = self.module.get_import_info(class_name)
                return import_info
        return None

    def get_type(self) -> Tuple[str, bool]:
        """Get column type and whether the type was explicitly defined"""
        # Return real type if set
        for decorator in self.column_decorators:
            decorator_args = decorator["decorator_args"]
            if len(decorator_args) >= 1 and isinstance(decorator_args[0], str):
                # Get type from first argument of decorator
                return decorator_args[0], True

            # Look for type in column options
            for arg in decorator_args:
                item = arg
                # If type is nested deep under a ParseResults object, try to find it
                while isinstance(item, ParseResults):
                    if "type" in item:
                        return item["type"], True
                    item = item[0]

        # Fall back to TypeScript type of property
        return self.prop["type_annotation"][0], False

    @property
    def type(self) -> str:
        """Get column type"""
        return self.get_type()[0]

    @property
    def is_nullable(self) -> bool:
        """Get whether column is nullable"""
        for decorator in self.column_decorators:
            decorator_args = decorator[1:]
            for arg in decorator_args:
                if isinstance(arg, ParseResults) and "nullable" in arg:
                    return arg["nullable"]
        return False

    @property
    def is_primary_key(self) -> bool:
        """Get whether the column is a primary key"""
        # Matches PrimaryColumn and PrimaryGeneratedColumn
        return any(
            d["decorator_name"].startswith("Primary") for d in self.column_decorators
        )

    def for_dapi(self) -> DictType[str, Any]:
        """Return the column as a dictionary for DAPI"""
        return {
            "name": self.name,
            "data_type": self.type,
            "is_nullable": self.is_nullable,
        }

    def is_foreign_key(self) -> bool:
        """Return whether the column is a foreign key"""
        return self.relation_decorator is not None

    def get_referent(
        self,
    ) -> OptionalType[Tuple[str, OptionalType[str], OptionalType[Dict]]]:
        """Get name of the table and column that the column references

        Returns a tuple containing the name of the referent table and the name
        of the referent column, if specified.
        """
        if not self.is_foreign_key():
            return None

        first_arg = self.relation_decorator[1]
        if len(first_arg) == 1:
            # () => Table
            table = first_arg[0]
        else:
            # (type) => Table
            table = first_arg[1]

        import_info = self.module.get_import_info(table)

        for decorator in self.column_decorators:
            if decorator[0] != "JoinColumn":
                continue
            decorator_args = decorator[1:]
            for arg in decorator_args:
                if isinstance(arg, ParseResults) and "referencedColumnName" in arg:
                    return table, arg["referencedColumnName"], import_info

        return table, None, import_info

    def is_explicit_name(self) -> bool:
        """Return whether the column name was explicitly defined"""
        return self.get_name()[1]

    def is_explicit_type(self) -> bool:
        """Return whether the column type was explicitly defined"""
        return self.get_type()[1]

    def process_foreign_key_column(
        self, tables: List["Table"]
    ) -> Tuple[OptionalType[str], OptionalType[str]]:
        """Process a foreign key column to find the real type and name of the column"""
        referent_table_name, referent_column_name, referent_table_import_info = (
            self.get_referent()
        )
        referent_table = Table.find_by_imported_name_in_modules(
            tables, referent_table_name, referent_table_import_info["module_name"]
        )
        # Get if the real_name and real_type are already set
        real_name = getattr(self, "real_name", None)
        real_type = getattr(self, "real_type", None)
        if referent_table is not None:
            if referent_column_name is not None:
                referent_column = referent_table.columns.get(referent_column_name)
                if referent_column is not None and not self.is_explicit_type():
                    real_type = referent_column.type
            elif len(referent_table.primary_keys) == 1:
                referent_column_name = referent_table.primary_keys[0].name
                if referent_column_name is not None and not self.is_explicit_type():
                    real_type = referent_table.primary_keys[0].type
                if not self.is_explicit_name():
                    real_name = (
                        self.name
                        + referent_column_name[0].upper()
                        + referent_column_name[1:]
                    )
        return real_name, real_type


@dataclass
class Table:
    """Class for tables defined as TypeORM models"""

    module: Module
    project_path: str
    org_name_snakecase: str
    project: PackageScopedProjectInfo
    entity: ParseResults

    @property
    def filename(self) -> str:
        """Get the filename of the module"""
        return self.module.filename

    @property
    def class_name(self) -> str:
        """Get the class name of the entity"""
        return self.entity["class_name"]

    @property
    def name(self) -> str:
        """Get the table name"""
        decorators = self.entity.asDict().get("entity_decorators", [])

        for decorator in decorators:
            decorator_name = decorator.get("decorator_name")
            decorator_args = decorator.get("decorator_args", [])
            if decorator_name == "Entity" and len(decorator_args) > 0:
                arg = decorator_args[0]
                if isinstance(arg, str):
                    return arg
                if isinstance(arg, dict) and "name" in arg:
                    return arg["name"]

        return self.entity["class_name"]

    @property
    def base_class_info(self) -> OptionalType[DictType[str, OptionalType[str]]]:
        """Get the base class of the table and its file path"""
        base_class = self.entity.get("base_class")
        if base_class is None:
            return None

        result = self.module.get_import_info(base_class)
        return result

    @property
    def is_abstract(self) -> bool:
        """Return whether the table is abstract"""
        return self.entity.get("is_abstract", False)

    @property
    def is_entity(self) -> bool:
        """Return whether the table is an entity"""
        return any(
            d["decorator_name"] == "Entity" for d in self.entity["entity_decorators"]
        )

    @property
    def is_really_a_table(self) -> bool:
        """Return whether the entity model is actually a table"""
        return self.is_entity and not self.is_abstract

    @property
    def is_in_allowlist(self) -> bool:
        """Return whether the table is in the allowlist"""
        return self.project.is_model_included(
            self.name,
            self.filename,
        )

    @classmethod
    def find_by_imported_name_in_modules(
        cls, tables: List["Table"], imported_cls_name: str, module_name: str
    ) -> OptionalType["Table"]:
        """Find a table by name in a list of tables"""
        for table in tables:
            if (
                table.class_name == imported_cls_name
                and module_name
                and module_name in (table.module.module_name, table.module.filename)
            ):
                return table
        return None

    @cached_property
    def columns(self) -> DictType[str, Column]:
        """Return columns for table as a list of Column objects"""
        columns = {}

        properties = self.entity.get("properties", [])
        for prop in properties:
            prop_decorators = prop.get("decorators", [])

            column_decorator = None
            relation_decorator = None
            backup_column_decorator = None
            for decorator in prop_decorators:
                decorator_name = decorator["decorator_name"]
                if "Column" in decorator_name:
                    column_decorator = decorator
                elif decorator_name == "ManyToOne":
                    relation_decorator = decorator
                    # ManyToOne does not require JoinColumn to exist, so we will infer
                    backup_column_decorator = decorator
                elif decorator_name == "OneToOne":
                    # OneToOne requires JoinColumn decorator to exist
                    relation_decorator = decorator
                elif decorator_name in {"ManyToMany", "OneToMany"}:
                    # ManyToMany creates the mapping in a separate table, unsupported for now
                    # OneToMany is not a real column, so we can skip it
                    break

            if column_decorator is None and not backup_column_decorator:
                continue

            column = Column(
                prop,
                [column_decorator or backup_column_decorator],
                self.module,
                relation_decorator=relation_decorator,
            )

            if column.name in columns:
                existing_column = columns[column.name]
                existing_column.column_decorators.append(column_decorator)
                if relation_decorator is not None:
                    existing_column.relation_decorator = relation_decorator
            else:
                columns[column.name] = column
        return columns

    def get_columns(self) -> List[Column]:
        """Get the columns for the table"""
        return list(self.columns.values())

    @property
    def primary_keys(self) -> List[Column]:
        """Return the primary keys for the table"""
        return [column for column in self.get_columns() if column.is_primary_key]

    def construct_urn(self) -> str:
        """Construct URN for table"""
        return f"{self.org_name_snakecase}.typeorm.{self.project_name}.{self.name}"

    def construct_datastores(self) -> List[str]:
        """Get the datastores for the table."""
        playbooks = self.project.config.playbooks
        return JsProjectsDapiValidatorBase.add_non_playbook_datastore_fields(
            construct_dapi_source_sink_from_playbooks(playbooks, self.name)
            if playbooks
            else {"sources": [], "sinks": []}
        )

    def construct_team_urn(self) -> OptionalType[str]:
        """Construct the team URN for the table."""
        playbooks = self.project.config.playbooks
        return (
            construct_owner_team_urn_from_playbooks(playbooks, self.name, self.filename)
            if playbooks
            else None
        )

    @property
    def project_name(self) -> str:
        """Get the name of the application."""
        return os.path.basename(self.project_path)


@dataclass
class ProcessedColumn(Column):
    """Processed column with real name and type for foreign keys and embedded entities"""

    # real_name and real_type are set after figuring out the referenced entity in foreign keys
    real_name: OptionalType[str] = None
    real_type: OptionalType[str] = None
    # replace the column with columns from the embedded entity
    embedded_entity_table: OptionalType[Table] = None

    def get_name(self) -> Tuple[str, bool]:
        return super().get_name() if self.real_name is None else (self.real_name, True)

    def get_type(self) -> Tuple[str, bool]:
        return super().get_type() if self.real_type is None else (self.real_type, True)


@dataclass
class ProcessedTable(Table):
    """Processed table with processed columns and base class table"""

    processed_columns: OptionalType[List[ProcessedColumn]] = None
    base_class_table: OptionalType[Table] = None

    def get_columns(self) -> List[ProcessedColumn]:
        """Return the processed columns as columns for the table"""
        return self.processed_columns or []

    def compile_columns(
        self, processed_tables: List["ProcessedTable"]
    ) -> List[ProcessedColumn]:
        """Get all columns including inherited and embedded columns"""
        all_columns = []
        for column in self.processed_columns:
            if column.embedded_entity_table is not None:
                embedded_table = self.find_by_imported_name_in_modules(
                    processed_tables,
                    column.embedded_entity_table.name,
                    column.embedded_entity_table.module.filename,
                )
                if embedded_table is not None:
                    embedded_columns = embedded_table.compile_columns(processed_tables)
                    for embedded_column in embedded_columns:
                        # Add the embedded column to the list after renaming it
                        # previousName + first -> previousNameFirst
                        # Make a copy of the column to avoid modifying the original
                        copy_column = ProcessedColumn(**asdict(embedded_column))
                        copy_column.real_name = (
                            column.name + embedded_column.name.capitalize()
                        )
                        all_columns.append(copy_column)
            else:
                all_columns.append(column)

        # Add columns from base class if any
        if self.base_class_table:
            base_class_processed_table = self.find_by_imported_name_in_modules(
                processed_tables,
                self.base_class_table.name,
                self.base_class_table.module.filename,
            )
            if base_class_processed_table is not None:
                base_class_columns = base_class_processed_table.compile_columns(
                    processed_tables
                )
                for column in base_class_columns:
                    if column.name not in [c.name for c in all_columns]:
                        all_columns.append(column)

        return all_columns


class TypeOrmDapiValidator(JsProjectsDapiValidatorBase):
    """
    Validator class for DAPI files created for TypeORM (TypeScript) models

    Supports
        - Typical Entity declaration
        - OneToOne, ManyToOne, and OneToMany relationships
        - Entity inheritance
        - Embedded entities

    UnSupported:
        - ManyToMany relationships because they create a mapping table
        - Single Table Inheritence (i.e. ChildEntity) as we need to manage polymorphism
        - Default exports out a module if it is imported with a different name in another
    """

    INTEGRATION_NAME = ORMIntegration.TYPEORM
    LOOKUP_FILE_SUFFIXES = [".ts"]

    # Only parse files if they contain any of these keywords, to limit the number of files parsed
    CHECK_KEYWORD_IN_FILE = ["Column", "ManyToOne", "OneToOne", "OneToMany", "Entity"]
    CHECK_KEYWORD_IN_FILENAME = ["entity", "model"]

    def find_tables(  # pylint: disable=too-many-locals
        self, filename: str, content: str, project: PackageScopedProjectInfo
    ) -> List[Table]:
        """Find TypeORM tables in a file"""
        # Define the grammar for TypeORM model
        identifier = Word(alphas + "_", alphas + "_" + "0123456789")
        identifier_with_spaces = Word(alphas + "_", alphas + "_" + "0123456789 ")
        data_modifiers = Keyword("public") | Keyword("private") | Keyword("protected")

        # Define the basic elements
        true_ = Keyword("true").setParseAction(replaceWith(True))
        false_ = Keyword("false").setParseAction(replaceWith(False))
        null_ = Keyword("null").setParseAction(replaceWith(None))

        # Define the basic types
        string_ = QuotedString('"') | QuotedString("'")
        number_ = pyparsing_common.number

        new_object = Keyword("new") + identifier + nested_expr("(", ")")

        # Define the lambda parameters with optional parentheses
        lambda_params = (
            identifier
            | (Suppress("(") + Optional(DelimitedList(identifier)) + Suppress(")"))
            | nested_expr("(", ")")
        )

        # Identifiers
        identifier_with_dots = Word(alphas + "_", alphas + "_" + "0123456789.")
        method_call = identifier_with_dots + nested_expr("(", ")")

        # Define the object and array structures
        object_ = Forward()
        array_ = Forward()
        lambda_function = Forward()

        # Any value
        value_ = Forward()

        all_types = (
            number_
            | true_
            | false_
            | null_
            | object_
            | array_
            | string_
            | new_object
            | lambda_function("lambda_function")
            | method_call
            | identifier_with_dots
            | identifier
        )

        # Conditional expression
        # Forward declarations
        conditional_expr = Forward()

        # Operators
        question = Suppress("?")
        colon = Suppress(":")
        # Comparison operators
        comparison_operator = Keyword("=") | Keyword(">") | Keyword("<") | Keyword("!")

        # Expression grammar
        operand = (
            identifier_with_dots
            | all_types
            | Group(Suppress("(") + conditional_expr + Suppress(")"))
        )
        conditional_expr << Group(
            Suppress(operand)
            + Suppress(ZeroOrMore(comparison_operator))
            + Optional(Suppress(operand))
            + question
            + operand("conditional_first_expr")
            + colon
            + operand("conditional_second_expr")
        )

        # Define the value types
        value_ << (conditional_expr | all_types)

        # Define the key-value pair in an object
        member_ = Group((string_ | identifier) + Suppress(":") + value_)

        # Define the object
        object_ << Group(
            Suppress("{")
            + Optional(Dict(DelimitedList(member_, allow_trailing_delim=True)))
            + Suppress("}")
        )

        # Define the array
        array_ << Group(
            Suppress("[")
            + Optional(DelimitedList(value_, allow_trailing_delim=True))
            + Suppress("]")
        )

        # Define the lambda function
        lambda_function << Group(
            lambda_params + Suppress("=>") + (value_ | nested_expr("{", "}"))
        )

        # Define import statements
        import_statement = Group(
            Keyword("import")
            + Optional(Suppress("{"))
            + DelimitedList(
                identifier_with_spaces, delim=LineEnd() | ",", allow_trailing_delim=True
            )("import_names")
            + Optional(Suppress("}"))
            + Suppress(Keyword("from"))
            + string_("import_from")
            + Suppress(";")
        )

        # Decorator can be a function call with optional arguments
        column_keyword = (
            Keyword("Column")
            | Keyword("PrimaryColumn")
            | Keyword("PrimaryGeneratedColumn")
            | Keyword("CreateDateColumn")
            | Keyword("UpdateDateColumn")
            | Keyword("DeleteDateColumn")
            | Keyword("VersionColumn")
            | Keyword("JoinColumn")
            | Keyword("ManyToOne")
            | Keyword("ManyToMany")
            | Keyword("OneToOne")
        )
        property_decorator = Suppress("@") + Group(
            (
                column_keyword("decorator_name")
                + Optional(
                    Suppress("(") + Optional(DelimitedList(value_)) + Suppress(")")
                )("decorator_args")
            )
            | (
                identifier("decorator_name")
                + Optional(nested_expr("(", ")"))("decorator_args")
            )
        )
        type_annotation = (
            Suppress(":")
            + identifier
            + Optional(Suppress(Keyword("is")))
            + Optional(Suppress(identifier))
            + Optional(Suppress("<") + identifier + Suppress(">"))
            + Optional(Suppress("|") + Suppress(identifier))
        )

        property_default = Suppress("=") + value_

        # Property declaration can end with a semicolon and can be a list
        property_declaration = Group(
            Group(ZeroOrMore(property_decorator))("decorators")
            + Optional(data_modifiers)("data_modifiers")
            + identifier("property_name")
            + Optional(Suppress("?"))
            + Optional(Suppress("!"))
            + Optional(type_annotation)("type_annotation")
            + Optional("[]")
            + Optional(Suppress(property_default))
            + Optional(Suppress(";"))
        )

        method_parameters = nested_expr("(", ")")
        method_return_type = type_annotation + Optional(
            Suppress("=>") + type_annotation
        )
        method_body = nested_expr("{", "}")
        method_declaration = Group(
            Group(ZeroOrMore(property_decorator))("decorators")
            + Optional(data_modifiers)("data_modifiers")
            + identifier
            + method_parameters
            + Optional(method_return_type)
            + method_body
            + Optional(Suppress(";"))
        )

        entity_class_decorator = Suppress("@") + Group(
            identifier("decorator_name")
            + Optional(Suppress("(") + Optional(DelimitedList(value_)) + Suppress(")"))(
                "decorator_args"
            )
        )

        entity_class_declaration = (
            Suppress(Keyword("export"))
            + Optional(Keyword("abstract")("is_abstract"))
            + Optional(Keyword("default")("is_default"))
            + Suppress(Keyword("class"))
            + identifier("class_name")
            + Optional(Suppress(Keyword("extends")) + identifier("base_class"))
        )

        entity_declaration = Group(
            Group(ZeroOrMore(entity_class_decorator))("entity_decorators")
            + entity_class_declaration
            + Suppress("{")
            + Group(ZeroOrMore(Suppress(method_declaration) | property_declaration))(
                "properties"
            )
            + Suppress("}")
        )

        # Define the grammar for TypeORM models
        model_declaration = OneOrMore(entity_declaration)

        # Define the grammar for JavaScript comments
        model_declaration.ignore(cpp_style_comment)

        # Parse the TypeORM model
        results = model_declaration.search_string(content)
        entities = sum(results) if len(results) > 0 else []

        imports_declaration = ZeroOrMore(import_statement)
        imports_declaration.ignore(cpp_style_comment)
        results = imports_declaration.search_string(content)
        imports = sum(results) if len(results) > 0 else []

        tables = []
        # Extract table names, column names, decorators, and column types
        for entity in entities:
            tables.append(
                Table(
                    Module(imports, filename),
                    project.full_path,
                    self.config.org_name_snakecase,
                    project,
                    entity,
                )
            )
        return tables

    def get_typeorm_entities(self) -> List[Table]:
        """Get all TypeORM tables found in project as a list of Table objects"""
        tables = []

        for project in self.get_all_projects():
            for filename, content in project.file_contents.items():
                if any(
                    keyword in content for keyword in self.CHECK_KEYWORD_IN_FILE
                ) or any(
                    keyword in filename for keyword in self.CHECK_KEYWORD_IN_FILENAME
                ):
                    tables += self.find_tables(filename, content, project)

        return tables

    def process_tables_globally(self, tables: List[Table]) -> List[ProcessedTable]:
        """Process tables globally to handle inheritance and embedded entities"""
        processed_tables = []
        # Try to find real types for foreign keys without explicit types
        for table in tables:
            # Process table for inheritance
            base_class_table = (
                Table.find_by_imported_name_in_modules(
                    tables,
                    table.base_class_info["class"],
                    table.base_class_info["module_name"],
                )
                if table.base_class_info is not None
                else None
            )

            # Process columns
            processed_columns: List[ProcessedColumn] = []
            for column in table.columns.values():
                # Set embedded_entity table to column
                real_type = column.type
                real_name = column.name
                embedded_entity_table = (
                    Table.find_by_imported_name_in_modules(
                        tables,
                        column.embedded_entity["class"],
                        column.embedded_entity["module_name"],
                    )
                    if column.embedded_entity is not None
                    else None
                )

                # Process foreign key columns with references to other tables
                if column.is_foreign_key():
                    real_name, real_type = column.process_foreign_key_column(tables)

                processed_columns.append(
                    ProcessedColumn(
                        prop=column.prop,
                        column_decorators=column.column_decorators,
                        module=column.module,
                        relation_decorator=column.relation_decorator,
                        real_name=real_name,
                        real_type=real_type,
                        embedded_entity_table=embedded_entity_table,
                    )
                )

            processed_tables.append(
                ProcessedTable(
                    module=table.module,
                    project_path=table.project_path,
                    org_name_snakecase=table.org_name_snakecase,
                    project=table.project,
                    entity=table.entity,
                    processed_columns=processed_columns,
                    base_class_table=base_class_table,
                )
            )

        # Compile columns recursively using above information
        for processed_table in processed_tables:
            processed_table.processed_columns = processed_table.compile_columns(
                processed_tables
            )

        # Redo foreign key associations after inheritence and embedded entities are processed
        for processed_table in processed_tables:
            compiled_columns = processed_table.processed_columns
            collect_columns: Dict[str, ProcessedColumn] = {}
            for column in compiled_columns:
                if column.is_foreign_key():
                    column.real_name, column.real_type = (
                        column.process_foreign_key_column(processed_tables)
                    )
                # Merge columns (& decorators) with same name
                if column.name in collect_columns:
                    existing_column = collect_columns[column.name]
                    column.column_decorators += existing_column.column_decorators
                    column.relation_decorator = (
                        column.relation_decorator or existing_column.relation_decorator
                    )
                collect_columns[column.name] = column
            processed_table.processed_columns = list(collect_columns.values())
        return processed_tables

    def _get_base_generated_files(self) -> DictType[str, DictType]:
        """Generate base template for autoupdate"""
        processed_tables = self.process_tables_globally(self.get_typeorm_entities())
        result = {}
        for table in processed_tables:
            if not table.is_really_a_table or not table.is_in_allowlist:
                continue

            dapi_location = table.project.construct_dapi_location(table.name)

            result[dapi_location] = self.add_default_non_generated_schema_portions(
                {
                    "urn": table.construct_urn(),
                    "owner_team_urn": table.construct_team_urn(),
                    "datastores": table.construct_datastores(),
                    "fields": [
                        field.for_dapi()
                        for field in table.compile_columns(processed_tables)
                    ],
                    "primary_key": [c.name for c in table.primary_keys],
                    "context": {
                        "service": table.project_name,
                        "integration": "typeorm",
                        "rel_model_path": os.path.relpath(
                            table.filename, dapi_location
                        ),
                    },
                }
            )

        return result
