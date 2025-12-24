# pylint: disable=duplicate-code, too-many-locals
"""Sequelize v6 DAPI validator module"""
import functools
import os.path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import esprima
import esprima.nodes as nd

from opendapi.config import (
    construct_dapi_source_sink_from_playbooks,
    construct_owner_team_urn_from_playbooks,
)
from opendapi.models import PlaybookConfig
from opendapi.validators.dapi.base.js import JsProjectsDapiValidatorBase
from opendapi.validators.dapi.base.main import ORMIntegration
from opendapi.validators.dapi.models import PackageScopedProjectInfo


class ParseException(Exception):
    """Exception raised if there is an issue parsing a file"""


@dataclass
class Column:
    """Data class for a column in a Sequelize v6 table"""

    node: nd.Node

    def __post_init__(self) -> None:
        self.props: Dict[str, nd.Node] = {}
        if isinstance(self.node.value, nd.ObjectExpression):
            for prop in self.node.value.properties:
                self.props[prop.key.name] = prop.value
        else:
            self.props["type"] = self.node.value

    @property
    def name(self) -> str:
        """Get column name"""
        if "field" in self.props:
            field = self.props["field"]
            return field.value
        return self.node.key.name

    @property
    def type(self) -> str:
        """Get column type"""
        prop = self.props["type"]
        if (
            isinstance(prop, nd.StaticMemberExpression)
            and isinstance(prop.object, nd.Identifier)
            and prop.object.name == "DataTypes"
        ):
            # e.g. `DataTypes.STRING` => STRING
            return prop.property.name
        if (
            isinstance(prop, nd.CallExpression)
            and isinstance(prop.callee, nd.StaticMemberExpression)
            and isinstance(prop.callee.object, nd.Identifier)
            and prop.callee.object.name == "DataTypes"
        ):
            # e.g. `DataTypes.STRING(100)` => STRING
            return prop.callee.property.name
        if (
            isinstance(prop, nd.StaticMemberExpression)
            and isinstance(prop.object, nd.StaticMemberExpression)
            and isinstance(prop.object.object, nd.Identifier)
            and prop.object.object.name == "DataTypes"
        ):
            # e.g. `DataTypes.STRING.BINARY` => STRING
            return prop.object.property.name
        if (
            isinstance(prop, nd.StaticMemberExpression)
            and isinstance(prop.object, nd.CallExpression)
            and isinstance(prop.object.callee, nd.StaticMemberExpression)
            and isinstance(prop.object.callee.object, nd.Identifier)
            and prop.object.callee.object.name == "DataTypes"
        ):
            # e.g. `DataTypes.STRING(100).BINARY` => STRING
            return prop.object.callee.property.name
        raise ParseException(f"Could not parse data type for column '{self.name}'")

    @property
    def is_nullable(self) -> bool:
        """Get whether columns is nullable"""
        if "allowNull" not in self.props:
            return True

        allow_null = self.props["allowNull"]
        return allow_null.value

    @property
    def is_primary_key(self) -> bool:
        """Get whether the column is a primary key"""
        if "primaryKey" not in self.props:
            return False

        primary_key = self.props["primaryKey"]
        return primary_key.value

    def for_dapi(self) -> Dict[str, Any]:
        """Return the column as a dictionary for DAPI"""
        return {
            "name": self.name,
            "data_type": self.type,
            "is_nullable": self.is_nullable,
        }


@dataclass
class Table(ABC):
    """Base class for tables defined as Sequelize v6 models"""

    filename: str
    app_full_path: str
    org_name_snakecase: str
    playbooks: Optional[List[PlaybookConfig]]
    project: PackageScopedProjectInfo

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the table name"""

    @abstractmethod
    def get_column_attributes_object(self) -> nd.ObjectExpression:
        """Get ObjectExpression node containing all columns for the table"""

    @property
    def columns(self) -> List[Column]:
        """Return columns for table as a list of Column objects"""
        columns = []

        attributes = self.get_column_attributes_object()
        for node in attributes.properties:
            columns.append(Column(node))

        return columns

    def construct_dapi_location(self) -> str:
        """Construct the DAPI location for the table."""
        return self.project.construct_dapi_location(self.name)

    def construct_urn(self) -> str:
        """Construct URN for table"""
        return f"{self.org_name_snakecase}.sequelize.{self.app_name}.{self.name}"

    def construct_datastores(self) -> List[str]:
        """Get the datastores for the table."""
        return JsProjectsDapiValidatorBase.add_non_playbook_datastore_fields(
            construct_dapi_source_sink_from_playbooks(self.playbooks, self.name)
            if self.playbooks
            else {"sources": [], "sinks": []}
        )

    def construct_team_urn(self) -> Optional[str]:
        """Construct the team URN for the table."""
        return (
            construct_owner_team_urn_from_playbooks(
                self.playbooks, self.name, self.filename
            )
            if self.playbooks
            else None
        )

    @property
    def app_name(self) -> str:
        """Get the name of the application."""
        return os.path.basename(self.app_full_path)


@dataclass
class SequelizeDefineTable(Table):
    """Data class for a table created by calling `sequelize.define`"""

    node: nd.CallExpression
    """The node corresponding to the `sequelize.define()` call"""

    @property
    def name(self) -> str:
        return self.node.arguments[0].value

    def get_column_attributes_object(self) -> nd.ObjectExpression:
        return self.node.arguments[1]


@dataclass
class ExtendModelTable(Table):
    """Data class for a table created by extending Model and calling `init`"""

    class_name: str
    node: nd.CallExpression
    """The node corresponding to the `MyModel.init()` call"""

    def __post_init__(self) -> None:
        self.opts: Dict[str, nd.Node] = {}
        for prop in self.node.arguments[1].properties:
            self.opts[prop.key.name] = prop.value

    @property
    def name(self) -> str:
        if "modelName" in self.opts:
            model_name = self.opts["modelName"]
            return model_name.value
        return self.class_name

    def get_column_attributes_object(self) -> nd.ObjectExpression:
        return self.node.arguments[0]


class SequelizeDapiValidator(JsProjectsDapiValidatorBase):
    """Validator class for DAPI files created for Sequelize v6 models"""

    INTEGRATION_NAME = ORMIntegration.SEQUELIZE
    LOOKUP_FILE_SUFFIXES: List[str] = [".js"]

    @staticmethod
    def is_sequelize_define_call(node) -> bool:
        """Return whether the node is a `sequelize.define()` call"""
        return (
            isinstance(node, nd.CallExpression)
            and isinstance(node.callee, nd.StaticMemberExpression)
            and isinstance(node.callee.object, nd.Identifier)
            and node.callee.object.name == "sequelize"
            and isinstance(node.callee.property, nd.Identifier)
            and node.callee.property.name == "define"
        )

    @staticmethod
    def is_class_extends_model_declaration(node) -> bool:
        """Return whether the node is a `class MyModel extends Model` declaration"""
        return (
            isinstance(node, nd.ClassDeclaration)
            and isinstance(node.superClass, nd.Identifier)
            and node.superClass.name == "Model"
        )

    @staticmethod
    def is_model_init_call(node):
        """Return whether the node is a `MyModel.init()` call"""
        return (
            isinstance(node, nd.CallExpression)
            and isinstance(node.callee, nd.StaticMemberExpression)
            and isinstance(node.callee.property, nd.Identifier)
            and node.callee.property.name == "init"
        )

    def get_sequelize_tables(self) -> List[Table]:
        """Get all Sequelize tables found in project as a list of Table objects"""
        tables: List[Table] = []
        model_classes: List[str] = []
        model_class_filenames: Dict[str, str] = {}
        model_class_nodes: Dict[str, nd.CallExpression] = {}

        projects = self.get_all_projects()
        file_configs = {}
        file_pkgs = {}

        for project in projects:
            for filename in project.file_contents:
                file_configs[filename] = project
                file_pkgs[filename] = project.full_path

        def delegate(filename, node, _):
            table_config = file_configs[filename]
            if self.is_sequelize_define_call(node):
                table = SequelizeDefineTable(
                    filename,
                    file_pkgs[filename],
                    self.config.org_name_snakecase,
                    table_config.config.playbooks,
                    project,
                    node,
                )

                if table_config.is_model_included(table.name, table.filename):
                    tables.append(table)

            if self.is_class_extends_model_declaration(node):
                model_classes.append(node.id.name)

            if self.is_model_init_call(node):
                model_class_filenames[node.callee.object.name] = filename
                model_class_nodes[node.callee.object.name] = node

        for project in projects:
            for filename, content in project.file_contents.items():
                lines = content.split("\n")
                if len(lines) > 0 and lines[0].startswith("#!"):
                    content = "\n".join(lines[1:])

                try:
                    esprima.parseModule(
                        content, delegate=functools.partial(delegate, filename)
                    )
                except esprima.Error:
                    pass

        for class_name in model_classes:
            if class_name not in model_class_nodes:
                continue
            table_config = file_configs.get(model_class_filenames[class_name], {})
            pkg_name = file_pkgs[model_class_filenames[class_name]]
            table = ExtendModelTable(
                model_class_filenames[class_name],
                pkg_name,
                self.config.org_name_snakecase,
                table_config.config.playbooks,
                project,
                class_name,
                model_class_nodes[class_name],
            )

            if table_config.is_model_included(
                table.name,
                table.filename,
            ):
                tables.append(table)
        return tables

    def _get_base_generated_files(self) -> Dict[str, Dict]:
        """Generate base template for autoupdate"""
        result = {}

        for table in self.get_sequelize_tables():
            result[table.construct_dapi_location()] = (
                self.add_default_non_generated_schema_portions(
                    {
                        "urn": table.construct_urn(),
                        "owner_team_urn": table.construct_team_urn(),
                        "datastores": table.construct_datastores(),
                        "fields": [field.for_dapi() for field in table.columns],
                        "primary_key": [
                            c.name for c in table.columns if c.is_primary_key
                        ],
                        "context": {
                            "service": table.app_name,
                            "integration": "sequelize",
                            "rel_model_path": os.path.relpath(
                                table.filename, table.construct_dapi_location()
                            ),
                        },
                    }
                )
            )

        return result
