# pylint: disable=no-member
"""Protobuf DAPI validator module"""

import copy
import functools
import importlib.resources
import json
import os
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Dict, List, Set, Tuple

from google.protobuf import descriptor_pb2
from google.protobuf.descriptor import FieldDescriptor
from grpc_tools import protoc

from opendapi.adapters.file import find_files_with_suffix
from opendapi.config import (
    construct_dapi_source_sink_from_playbooks,
    construct_owner_team_urn_from_playbooks,
    construct_project_full_path,
)
from opendapi.defs import OPENDAPI_SPEC_URL
from opendapi.models import ProjectConfig
from opendapi.validators.dapi.base.main import DapiValidator, ORMIntegration
from opendapi.validators.dapi.models import ProjectInfo
from opendapi.validators.defs import IntegrationType

########## constants ##########

# FieldDescriptor has vars named like TYPE_DOUBLE, etc. that are their corresponding ints
# - and we are then pruning the "enum"-like attr name to get the name of the type
_PROTOBUF_TYPE_MAP = {
    value: name.replace("TYPE_", "").lower()
    for name, value in vars(FieldDescriptor).items()
    if name.startswith("TYPE_")
}

_PRIMITIVE_TYPES = {
    "double",
    "float",
    "int64",
    "uint64",
    "int32",
    "fixed64",
    "fixed32",
    "bool",
    "string",
    "bytes",
    "uint32",
    "sfixed32",
    "sfixed64",
    "sint32",
    "sint64",
}

_WRAPPER_TYPE_MAP = {
    # NOTE we say that Any is an object, since its a oneof
    ".google.protobuf.Any": "object",
    ".google.protobuf.Timestamp": "datetime",
    # NOTE this is a json dict of json primitives
    #      we say its an object since its a oneof
    ".google.protobuf.Struct": "object",
    # NOTE this is a json array of json primitives
    #      we say its an array of objects since its an array of oneof
    ".google.protobuf.ListValue": "array<object>",
    # NOTE this is a json primitive - we say its an object
    #      since its a oneof
    ".google.protobuf.Value": "object",
    ".google.protobuf.DoubleValue": "double",
    ".google.protobuf.FloatValue": "float",
    ".google.protobuf.Int64Value": "int64",
    ".google.protobuf.UInt64Value": "uint64",
    ".google.protobuf.Int32Value": "int32",
    ".google.protobuf.UInt32Value": "uint32",
    ".google.protobuf.BoolValue": "bool",
    ".google.protobuf.StringValue": "string",
    ".google.protobuf.BytesValue": "bytes",
}

_LABEL_MAP = {
    value: name.replace("LABEL_", "").lower()
    for name, value in vars(FieldDescriptor).items()
    if name.startswith("LABEL_")
}


########## project info ##########


@dataclass
class ProtobufProjectInfo(ProjectInfo):
    """Protobuf project"""

    # NOTE other validators have one artifact per project path. We do not do that here since
    #      for protobuf, since there is no anchor, the project path serves as the anchor,
    #      and all of the proto packages are meant to go to the same location - so we handle them together.
    proto_package_names: Set[str] = dataclass_field(default_factory=set)

    @functools.cached_property
    def relative_proto_files(
        self,
    ) -> List[str]:
        """Get the proto files"""
        return [
            os.path.relpath(fp, self.root_path)
            for fp in find_files_with_suffix(self.full_path, [".proto"])
        ]

    @functools.cached_property
    def _fds(
        self,
    ) -> descriptor_pb2.FileDescriptorSet:
        """Compile proto to descriptor in memory"""
        with tempfile.NamedTemporaryFile() as temp_file:
            # NOTE: grpc tools does not make these readily accessible, since it doesnt
            #       access the path like a usual binary install?
            builtin_proto_path = os.path.relpath(
                importlib.resources.files("grpc_tools").joinpath("_proto"),
                os.getcwd(),
            )
            cmd = [
                # first is a dummy to mimic sys.argv[0]
                "",
                "--include_imports",
                # NOTE this is where the compiler looks for imports. we will just assume its
                #      from repo root.
                "--proto_path=.",
                # we will also make sure to have the builtins reachable
                f"--proto_path={builtin_proto_path}",
                # NOTE: if we want more fidelity/comments etc. we can include this,
                #       omitting for performance
                # "--include_source_info",
                f"--descriptor_set_out={temp_file.name}",  # output to stdout
            ]

            # should be handled in validate_projects - this is just here
            # to make debugging easier
            if not self.relative_proto_files:  # pragma: no cover
                raise ValueError(f"No proto files found in {self.full_path}")

            cmd.extend(self.relative_proto_files)

            # Run protoc, capture stdout (the descriptor set)
            protoc.main(cmd)

            # Parse it into a FileDescriptorSet
            fds = descriptor_pb2.FileDescriptorSet()
            fds.ParseFromString(temp_file.read())
            return fds

    @functools.cached_property
    def __type_name_to_message_and_enum(
        self,
    ) -> Tuple[
        Dict[str, descriptor_pb2.DescriptorProto],
        Dict[str, descriptor_pb2.EnumDescriptorProto],
    ]:
        # NOTE technically a package name can be repeated in a repo depending on
        #      how one compiles, but in our scenario since they tell us what to compile
        #      idt that this is an issue, even if they do that bad practice
        message_type_name_to_message = {}
        enum_type_name_to_enum = {}

        # NOTE protobuf type names when referenced internally have the leading periods
        def _populate_enum(
            cur_package: str, enum_type: descriptor_pb2.EnumDescriptorProto
        ):
            enum_type_name = f"{cur_package}.{enum_type.name}"
            enum_type_name_to_enum[enum_type_name] = enum_type

        def _populate_message(
            cur_package: str, message_type: descriptor_pb2.DescriptorProto
        ):
            message_type_name = f"{cur_package}.{message_type.name}"
            message_type_name_to_message[message_type_name] = message_type
            for nested in message_type.nested_type:
                _populate_message(message_type_name, nested)
            for nested in message_type.enum_type:  # pragma: no cover
                _populate_enum(cur_package, nested)

        for file_proto in self._fds.file:
            qualified_file_package = (
                f".{file_proto.package}" if file_proto.package else ""
            )
            for message_type in file_proto.message_type:
                _populate_message(qualified_file_package, message_type)
            for enum_type in file_proto.enum_type:
                _populate_enum(qualified_file_package, enum_type)
        return message_type_name_to_message, enum_type_name_to_enum

    @property
    def _type_name_to_message(
        self,
    ) -> Dict[str, descriptor_pb2.DescriptorProto]:
        """Get the type name to message and enum"""
        return self.__type_name_to_message_and_enum[0]

    @staticmethod
    def _hashable_message(
        message: descriptor_pb2.DescriptorProto,
    ) -> str:
        """Get the message to hash"""
        return message.SerializeToString()

    @functools.cached_property
    def _message_hash_to_type_name(
        self,
    ) -> Dict[descriptor_pb2.DescriptorProto, str]:
        """Get the message to type name"""
        return {
            # NOTE we have to do this since the objects are mutable and therefore not hashable,
            #      but we never mutate them, so this is okay
            self._hashable_message(message): type_name
            for type_name, message in self._type_name_to_message.items()
        }

    @property
    def _type_name_to_enum(
        self,
    ) -> Dict[str, descriptor_pb2.EnumDescriptorProto]:
        """Get the type name to enum"""
        return self.__type_name_to_message_and_enum[1]

    def _is_map_type(
        self,
        proto_field: descriptor_pb2.FieldDescriptorProto,
        nested_dapi_fields: list[dict],
    ) -> bool:
        # NOTE this takes some explaining. protobuf maps are serialized
        #      as a repeated message, where the message is autogenerated
        #      with a key and value field, and the naming is related
        #      to the map name.
        #      i.e. map<string, string> map_field_name = 1;
        #           will actually be serialized as
        #           message MapFieldNameEntry {
        #               string key = 1;
        #               string value = 2;
        #           }
        #           repeated MapFieldNameEntry map_field_name = 1;

        # not a message type, so not a map
        if proto_field.type_name not in self._type_name_to_message:
            return False

        els = proto_field.name.split("_")
        map_entry_name = "".join([el.capitalize() for el in els]) + "Entry"
        type_message = self._type_name_to_message[proto_field.type_name]
        return (
            # can be more than 2 if the value of the map is an object,
            # but we only care about the first 2
            len(nested_dapi_fields) >= 2
            and type_message.name == map_entry_name
            and nested_dapi_fields[0]["name"] == f"{proto_field.name}.key"
            and nested_dapi_fields[1]["name"] == f"{proto_field.name}.value"
        )

    def _get_dapi_field_with_nested_fields(
        self,
        proto_field: descriptor_pb2.FieldDescriptorProto,
        name_prefix: str = "",
    ) -> List[Dict]:
        """
        recursively get the dapi fields for a message
        """
        field_name = (
            f"{name_prefix}.{proto_field.name}" if name_prefix else proto_field.name
        )
        is_wrapper_type = proto_field.type_name in _WRAPPER_TYPE_MAP
        og_is_wrapper_type = _PROTOBUF_TYPE_MAP[proto_field.type] == "message"
        should_recurse = og_is_wrapper_type and not is_wrapper_type

        nested_dapi_fields = (
            self._get_dapi_fields_for_message(
                self._type_name_to_message[proto_field.type_name],
                name_prefix=field_name,
            )
            if should_recurse
            else []
        )

        field_type = (
            _WRAPPER_TYPE_MAP[proto_field.type_name]
            if is_wrapper_type
            else _PROTOBUF_TYPE_MAP[proto_field.type]
        )
        field_label = _LABEL_MAP[proto_field.label]

        # in the DB
        enum_info = {}
        if field_type == "enum":
            enum = self._type_name_to_enum[proto_field.type_name]
            values = [f"{value.name}={value.number}" for value in enum.value]
            enum_info = {
                "enum_values": values,
            }
            field_type = "enum<int32>"

        if is_map_type := self._is_map_type(proto_field, nested_dapi_fields):
            key = nested_dapi_fields[0]
            value = nested_dapi_fields[1]
            field_type = f"map<{key['data_type']}, {value['data_type']}>"
            map_field_name = f"{field_name}.{{*}}"
            for nf in nested_dapi_fields:
                nf["name"] = nf["name"].replace(field_name, map_field_name)

        elif field_type == "message":
            field_type = "object"

        if field_label == "repeated" and not is_map_type:
            field_type = f"array<{field_type}>"
            array_field_name = f"{field_name}.[*]"
            for nf in nested_dapi_fields:
                nf["name"] = nf["name"].replace(field_name, array_field_name)

        # NOTE order matters here, since we convert the wrapper
        #      to primitive types
        # NOTE what we try to distill is if None is a valid value, which differs
        #      for primitives, wrappers, and is_required etc. for proto2/proto3
        # NOTE oneof fields are special - they show up "raw" on the message, and each
        #      has a number associated with the actual message (not like a nested message or enum)
        #      - essentially they are all optional, and at runtime the there is a wrapper
        #      "@property" that sees which one is set and returns that value.
        #      i.e.
        #      message Review {
        #          string text = 1;
        #          oneof review {
        #              string text = 2;
        #              int32 stars = 3;
        #          }
        #      }
        #      each of them is part of the message, but at runtime one would access
        #      the attr named "review" and it would return either the text or stars,
        #      depending on which one is set.

        # lol proto3 added back optionals for scalars and does not change
        # the label from required.. so this has to be checked first and differently
        # TO MAKE MATTERS WORSE, internally this is a oneof of sorts - these have
        # `oneof_index` set to to a oneof! This technically then gets covered by the oneof
        # check below, but I wanted to include it explicitly - but therefore it just come first
        if proto_field.proto3_optional:
            nullability = True

        # as a descriptor, it is given a default value if it is not set, and as an
        # integer type that is 0, which would be the same as the first
        # oneof... so we have to use HasField to determine if it is a oneof
        # (proto getting rid of optionals was sorta dumb lol - they have walked
        #  it back a ton)
        elif proto_field.HasField("oneof_index"):
            nullability = True

        # in proto2, any messages that are required - even the wrapper types
        # (which are just messages) are not nullable
        # this does not apply to proto3
        # proto3 optional exists since they had to walk it back, but its different
        # so they didnt have to redo it... sigh dude.
        elif field_label == "required":
            nullability = False

        # repeated fields can never have null values, they will have the empty array
        elif field_label == "repeated":
            nullability = False

        # messages are allowed to be null if they are not required,
        # and wrappers are just messages
        elif og_is_wrapper_type:
            nullability = True

        # none is not a valid value for primitives
        elif field_type in _PRIMITIVE_TYPES:
            nullability = False

        # enums can never have null values - they are assigned defaults (0 I think)
        elif enum_info:
            nullability = False

        # we will default to saying things are not nullable
        else:  # pragma: no cover
            nullability = False

        return [
            {
                "name": field_name,
                "data_type": field_type,
                "is_nullable": nullability,
                **enum_info,
            }
        ] + nested_dapi_fields

    def _get_dapi_fields_for_message(
        self,
        message: descriptor_pb2.DescriptorProto,
        name_prefix: str = "",
    ) -> List[Dict]:
        dapi_fields = []
        for proto_field in message.field:
            dapi_fields.extend(
                self._get_dapi_field_with_nested_fields(
                    proto_field,
                    name_prefix=name_prefix,
                )
            )
        return dapi_fields

    def _get_qualified_table_name(
        self,
        message: descriptor_pb2.DescriptorProto,
    ) -> str:
        # NOTE each qualified table name starts with a period, so we remove it
        return self._message_hash_to_type_name[self._hashable_message(message)][1:]

    def _get_absolute_filename(self, relative_filename: str) -> str:
        """Get the absolute filename"""
        return os.path.join(self.root_path, relative_filename)

    def _create_dapi(
        self,
        message: descriptor_pb2.DescriptorProto,
        absolute_proto_filename: str,
        package: str,
        syntax: str,
    ) -> Dict:

        project_path = self.config.project_path
        project_path = project_path.replace("/", ".")
        project_path = project_path[:-1] if project_path.endswith(".") else project_path
        project_path = "" if self.full_path == self.root_path else f"{project_path}"
        # NOTE depending on how they orient their file, the project path may match the
        #      package name portion of the qualified table name, but we will leave this in
        #      case there are other packages that are in the same location
        qualified_table_name = self._get_qualified_table_name(message)
        return ProtobufDapiValidator.add_default_non_generated_schema_portions(
            {
                "schema": OPENDAPI_SPEC_URL.format(
                    version=ProtobufDapiValidator.SPEC_VERSION, entity="dapi"
                ),
                "urn": (
                    f"{self.org_name_snakecase}."
                    f"{ProtobufDapiValidator.INTEGRATION_NAME.value}."
                    f"{project_path}."
                    f"{qualified_table_name}"
                ),
                # NOTE we should add this in another PR. Most likely going to be a regex config.
                "primary_key": [],
                "owner_team_urn": (
                    construct_owner_team_urn_from_playbooks(
                        self.config.playbooks,
                        qualified_table_name,
                        absolute_proto_filename,
                    )
                    if self.config.playbooks
                    else None
                ),
                "datastores": ProtobufDapiValidator.add_non_playbook_datastore_fields(
                    construct_dapi_source_sink_from_playbooks(
                        self.config.playbooks,
                        qualified_table_name,
                    )
                    if self.config.playbooks
                    else {"sources": [], "sinks": []}
                ),
                "fields": self._get_dapi_fields_for_message(message),
                "context": {
                    "service": package,
                    "integration": "protobuf",
                    "rel_model_path": os.path.relpath(
                        absolute_proto_filename,
                        self.construct_dapi_location(qualified_table_name),
                    ),
                    "syntax": syntax,
                },
            }
        )

    def create_dapis(self) -> Dict[str, Dict]:
        """Create the DAPIs"""
        seen_packages = {file_proto.package for file_proto in self._fds.file}
        not_seen_packages = self.proto_package_names - seen_packages
        if not_seen_packages:
            not_seen_str = ", ".join(sorted(not_seen_packages))
            raise ValueError(
                f"The following packages were not found during compilation: {not_seen_str}"
            )

        return {
            self.construct_dapi_location(qualified_table_name): self._create_dapi(
                message,
                absolute_proto_filename,
                file_proto.package,
                # once again, since its a descriptor we are playing with
                # it gets a default value if its not set. thankfully that happens for proto2
                # and the default is empty string, so we dont need to do HasField nonsense
                file_proto.syntax or "proto2",
            )
            for file_proto in self._fds.file
            # we only want dapis for packages that we are interested in
            if file_proto.package in self.proto_package_names
            # these are just the top levels, so good there
            for message in file_proto.message_type
            # make sure that we consider the allow/exclude list
            if self.is_model_included(
                (qualified_table_name := self._get_qualified_table_name(message)),
                (
                    absolute_proto_filename := self._get_absolute_filename(
                        file_proto.name
                    )
                ),
            )
        }


########## validator ##########


class ProtobufDapiValidator(DapiValidator[ProtobufProjectInfo]):
    """
    Validator class for DAPIs created from DBT models

    NOTE: currently we re compile once for each project, but common imports are therefore
          compiled multiple times. this allows for nice project level isolation, but
          if we see performance issues we can reorganize to compile once for all projects
    """

    INTEGRATION_NAME = ORMIntegration.PROTOBUF
    INTEGRATION_TYPE = IntegrationType.STATIC

    ########## project related ##########

    def validate_projects(self, projects: List[ProtobufProjectInfo]):
        """Validate the projects"""
        projects_missing_packages = set()
        packages_to_projects = defaultdict(set)
        projects_without_proto_files = set()
        for project in projects:
            if not project.proto_package_names:
                projects_missing_packages.add(project.full_path)

            if not project.relative_proto_files:
                projects_without_proto_files.add(project.full_path)

            for package in project.proto_package_names:
                packages_to_projects[package].add(project.full_path)

        errors = []
        if projects_missing_packages:
            errors.append(
                f"Projects {projects_missing_packages} are missing proto packages, "
                f"which should be a comma delimited list under artifact_path"
            )
        if projects_without_proto_files:
            errors.append(
                f"Projects {projects_without_proto_files} are missing proto files"
            )

        repeated_packages = {
            package: sorted(projects)
            for package, projects in packages_to_projects.items()
            if len(projects) > 1
        }
        if repeated_packages:
            errors.append(
                f"Packages {json.dumps(repeated_packages)} are repeated across projects"
            )
        if errors:
            raise ValueError("\n".join(errors))

    def get_all_projects(self) -> List[ProtobufProjectInfo]:
        """
        Get projects from all protobuf files.

        NOTE: this is not supported for protobuf, since the assumption
              is that most proto files do not contain events, and since
              we lack an "anchor" to place the dapis at, and so we require
              overrides to communicate this.
        """
        raise RuntimeError("get_all_projects is not supported for Protobuf")

    def get_project(self, project_config: ProjectConfig) -> ProtobufProjectInfo:
        """Given a project config, return ProjectInfo object"""

        copy_project_config = copy.deepcopy(project_config)
        # proto output does not include leading dots, but those are valid,
        # so we remove them for consistency
        # NOTE not existing or the empty string is valid, since that is how we refer
        #      to the default namespace
        # NOTE other validators have one artifact per project path. We do not do that here since
        #      for protobuf, since there is no anchor, the project path serves as the anchor,
        #      and all of the proto packages are meant to go to the same location - so we handle them together.
        proto_package_names = {
            package.lstrip(".")
            for package in (copy_project_config.artifact_path or "").split(",")
        }
        project_full_path = construct_project_full_path(
            self.root_dir, copy_project_config.project_path
        )
        copy_project_config.include_models = (
            copy_project_config.include_models or self.integration_config.include_models
        )
        # convert the model allowlist to the new format
        new_model_allowlist = []
        for entry in copy_project_config.model_allowlist:

            # models may be prefixed by package, so we remove the leading
            # period in this scenario
            if not entry.startswith("path:"):
                entry = (
                    "!" + entry[1:].lstrip("\\.")
                    if entry.startswith("!")
                    else entry.lstrip("\\.")
                )
            new_model_allowlist.append(entry)

        copy_project_config.model_allowlist = new_model_allowlist

        return ProtobufProjectInfo(
            org_name_snakecase=self.config.org_name_snakecase,
            root_path=self.root_dir,
            config=copy_project_config,
            full_path=project_full_path,
            proto_package_names=set(proto_package_names),
        )

    ########## base generated files ##########

    def _get_base_generated_files(self) -> Dict[str, Dict]:
        """Get the base generated files"""
        return {
            fp: dapi
            for project in self.selected_projects()
            for fp, dapi in project.create_dapis().items()
        }
