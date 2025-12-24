# pylint: disable=too-many-instance-attributes, no-name-in-module
"""Validator class for DAPI and related files"""

from __future__ import annotations

import functools
import os
from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
from typing import Dict, Iterable, List, Optional, Set, Tuple, Type, Union

import requests
from deepmerge import STRATEGY_END, Merger
from jsonschema_rs import ValidationError as JsonValidationError
from jsonschema_rs import validator_for as jsonschema_validator_for

from opendapi.adapters.file import find_files_with_suffix
from opendapi.adapters.git import ChangeTriggerEvent, GitCommitStasher
from opendapi.cli.common import Schemas
from opendapi.config import OpenDAPIConfig
from opendapi.defs import DEFAULT_DAPIS_DIR, CommitType, OpenDAPIEntity
from opendapi.logging import LogCounterKey, increment_counter
from opendapi.utils import (
    YAML,
    convert_ruemelyaml_commentedmap_to_dict,
    fetch_schema,
    prune_additional_properties,
    read_yaml_or_json,
)
from opendapi.validators.defs import (
    CollectedFile,
    FileSet,
    IntegrationType,
    MergeKeyCompositeIDParams,
    MultiValidationError,
    ValidationError,
)


@contextmanager
def _maybe_git_commit_stash(
    root_dir: str,
    commit_already_checked_out: bool,
    commit_type: CommitType,
    change_trigger_event: ChangeTriggerEvent,
):
    """Stash the git commit if necessary"""
    if commit_type is not CommitType.CURRENT and not commit_already_checked_out:
        commit_sha = change_trigger_event.commit_type_to_sha(commit_type)
        with GitCommitStasher(root_dir, "opendapi-validate", commit_sha):
            yield
    else:
        yield


class StrictTopLevelError(ValueError):
    """Error raised when top-level dicts differ"""


def _strict_toplevel_strategy(
    config, path, base, nxt
):  # pylint: disable=unused-argument
    """
    Only check at path == [] (top level).
    Prevent deepmerge from recursing by returning early.
    """
    # non-empty path -> deepmerge is trying to recurse -> block it
    if path:  # pragma: no cover
        raise RuntimeError("This Merger is shallow-only, recursion disabled")

    if base != nxt:
        raise StrictTopLevelError(f"Top-level dicts differ: {base!r} != {nxt!r}")

    return base


class BaseValidator(ABC):
    """Base validator class for DAPI and related files"""

    SUFFIX: List[str] = NotImplemented

    # if True, then the base and generated file states must be strictly equal
    STRICT_EQUALITY: bool = False

    # Paths & keys to use for uniqueness check within a list of dicts when merging
    MERGE_UNIQUE_LOOKUP_KEYS: List[
        Tuple[
            List[Union[str, int, MergeKeyCompositeIDParams.IgnoreListIndexType]],
            MergeKeyCompositeIDParams,
        ]
    ] = []

    # Paths to disallow new entries when merging
    MERGE_DISALLOW_NEW_ENTRIES_PATH: List[
        List[Union[str, int, MergeKeyCompositeIDParams.IgnoreListIndexType]]
    ] = []

    # For Non-DAPI files, we don't want to generate a file if a file of that entity type exists
    # (e.g. categories, purposes, etc.)
    # For DAPI files, we want to generate a file always
    MUST_GENERATE_EVEN_IF_ENTITY_TYPE_EXISTS: bool = True

    SPEC_VERSION: str = NotImplemented
    ENTITY: OpenDAPIEntity = NotImplemented
    INTEGRATION_TYPE: IntegrationType = IntegrationType.STATIC

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        root_dir: str,
        runtime: str,
        change_trigger_event: ChangeTriggerEvent,
        commit_type: CommitType,
        enforce_existence_at: Optional[FileSet] = None,
        override_config: Optional[OpenDAPIConfig] = None,
        schema_to_prune_generated: Optional[Dict] = None,
    ):
        self.schema_cache = {}
        self.yaml = YAML()
        self.root_dir = root_dir
        self.runtime = runtime
        self.change_trigger_event = change_trigger_event
        self.commit_type = commit_type
        self.enforce_existence_at = enforce_existence_at
        self.config: OpenDAPIConfig = override_config or OpenDAPIConfig(root_dir)
        self.schema_to_prune_generated = schema_to_prune_generated
        # helpers
        self._jsonschema_ref_to_validator = {}

        # we run file collection at __init__ time,
        # so that there is no confusion what the results will be if
        # collected_files is accessed later on
        _ = self.collected_files

    @property
    def commit_sha(self) -> Optional[str]:
        """Get the commit SHA"""
        # for current state, there is nothing to check out - otherwise we get the commit sha,
        # and we enforce that it exists
        return (
            None
            if self.commit_type is CommitType.CURRENT
            else self.change_trigger_event.commit_type_to_sha(self.commit_type)
        )

    @property
    def base_destination_dir(self) -> str:
        """Get the base directory for the spec files"""
        return os.path.join(self.root_dir, DEFAULT_DAPIS_DIR)

    @classmethod
    def merge(cls, base: Dict, nxt: Dict) -> Dict:
        """Merge the base and next dictionaries"""
        return cls._get_merger().merge(deepcopy(base), deepcopy(nxt))

    def get_file_state(self, fileset: FileSet) -> Dict[str, Dict]:
        """Get the file state at a given file set"""
        if fileset is FileSet.ORIGINAL:
            return self.original_file_state
        if fileset is FileSet.GENERATED:
            return self.generated_file_state
        if fileset is FileSet.MERGED:
            return self.merged_file_state
        raise ValueError(f"Invalid file set: {fileset}")  # pragma: no cover

    @classmethod
    def _get_merger(
        cls,
        merge_unique_lookup_keys_override: Optional[
            List[Tuple[List[str], MergeKeyCompositeIDParams]]
        ] = None,
    ):
        """
        Get the merger object for deepmerge

        NOTE: merge() mutates - defend if necessary
        """

        if cls.STRICT_EQUALITY:
            return Merger(
                [
                    (dict, [_strict_toplevel_strategy]),
                ],
                [_strict_toplevel_strategy],
                [_strict_toplevel_strategy],
            )

        def _autoupdate_merge_strategy_for_non_mergeable_lists(  # pylint: disable=unused-argument
            config, path, base, nxt
        ):
            """
            For non-mergeable lists - detected via the path being in MERGE_DISALLOW_NEW_ENTRIES_PATH
            - we just return the base
            """
            return base if path in cls.MERGE_DISALLOW_NEW_ENTRIES_PATH else STRATEGY_END

        def _get_match_using_merge_keys(
            list_to_match: List, itm: Dict, merge_keys: List[MergeKeyCompositeIDParams]
        ) -> Optional[Dict]:
            """
            Given a list of merge keys, find the first key present in itm, and return the
            first element from list_to_match that has the same value for that key.
            """

            key, id_ = MergeKeyCompositeIDParams.get_key_and_id(itm, merge_keys)
            return next(
                (n for n in list_to_match if key.get_id_if_matched(n) == id_),
                None,
            )

        def _autoupdate_merge_strategy_for_dict_lists(config, path, base, nxt):
            """
            To properly merge lists of dicts, and ensure that we do not miss any,
            we require that an ID be able to be derived for all elements in the list.

            Merging and deduping is done based on the ID.

            If folks do not want merging, and only want deduping, the ID can be set to
            the entire set of keys.

            NOTE: The one caveat introduced is that folks cant define their own list of dicts,
                  but we do this to ensure that we do not miss any merges.
            """
            # this strategy is called for all lists, we need to make sure it only applies for
            # lists of dicts
            base_all_dicts = all(isinstance(itm, dict) for itm in base)
            nxt_all_dicts = all(isinstance(itm, dict) for itm in nxt)
            not_both_list_dicts = not (base_all_dicts and nxt_all_dicts)
            # if the lists are empty then all returns true, so we need to account for that,
            # since they may not actually be lists of dicts
            both_empty = not base and not nxt
            if not_both_list_dicts or both_empty:
                return STRATEGY_END

            result = []
            merge_unique_lookup_keys = (
                merge_unique_lookup_keys_override or cls.MERGE_UNIQUE_LOOKUP_KEYS
            )
            autoupdate_unique_merge_keys_for_path = [
                v for k, v in merge_unique_lookup_keys if k == path
            ]

            # lets shy away from automatically deduping, and only scrub the
            # elements in nxt if they match some ID explicitly,
            # since otherwise we might miss merging when we should have.
            # This comes at the cost of allowing folks to have additional properties
            if not autoupdate_unique_merge_keys_for_path:
                raise ValueError(
                    f"Merging dicts lists needs to be explicitly defined for path {path}"
                )

            # oddity is that if base has multiple elements with the same ID, those are
            # allowed to remain separate
            for idx, itm in enumerate(base):
                matched_nxt_item = _get_match_using_merge_keys(
                    nxt, itm, autoupdate_unique_merge_keys_for_path
                )
                if matched_nxt_item:
                    result.append(
                        config.value_strategy(path + [idx], itm, matched_nxt_item)
                    )
                else:
                    result.append(itm)

            # sometimes we only want what is in base (merged) - i.e. for fields, we only want the
            # fields that are from the ORM. In that instance, just return the merged result
            # using only the keys present in base
            if path in cls.MERGE_DISALLOW_NEW_ENTRIES_PATH:
                return result

            present_ids = {
                MergeKeyCompositeIDParams.get_key_and_id(
                    el, autoupdate_unique_merge_keys_for_path
                )[1]
                for el in result
            }

            # we only append ones that are not already present in the result
            # (either from the merge step or if there are repeats within nxt)
            for itm in nxt:
                _, id_ = MergeKeyCompositeIDParams.get_key_and_id(
                    itm, autoupdate_unique_merge_keys_for_path
                )
                if id_ not in present_ids:
                    result.append(itm)
                    present_ids.add(id_)

            return result

        return Merger(
            [
                # NOTE: if we find one _autoupdate_merge_strategy_for_dict_lists restrictive,
                #       per class we can define classattr of various fns that do specific
                #       merging logic depending on path (if path doesnt match,
                #       return STRATEGY_END), and defaulting to `append_unique`
                #       should none match
                (
                    list,
                    [
                        _autoupdate_merge_strategy_for_dict_lists,
                        _autoupdate_merge_strategy_for_non_mergeable_lists,
                        "append_unique",
                    ],
                ),
                (dict, "merge"),
                (set, "union"),
            ],
            ["override"],
            ["override"],
        )

    def _get_files_for_suffix(self, suffixes: List[str]) -> List[str]:
        """Get all files in the root directory with given suffixes"""
        return find_files_with_suffix(self.root_dir, suffixes)

    def _read_yaml_or_json(self, file: str):
        """Read the file as yaml or json"""
        try:
            return read_yaml_or_json(file, self.yaml)
        except ValueError as exc:
            raise ValidationError(f"Unsupported file type for {file}") from exc

    def _get_file_contents_for_suffix(self, suffixes: List[str]):
        """Get the contents of all files in the root directory with given suffixes"""
        files = self._get_files_for_suffix(suffixes)
        return {file: self._read_yaml_or_json(file) for file in files}

    def validate_existance_at(self, override: Optional[FileSet] = None):
        """Validate that the files exist"""
        fileset_map = {
            FileSet.ORIGINAL: self.original_file_state,
            FileSet.GENERATED: self.generated_file_state,
            FileSet.MERGED: self.merged_file_state,
        }
        check_at = override or self.enforce_existence_at
        if check_at and not fileset_map[check_at]:
            raise ValidationError(
                f"OpenDAPI {self.__class__.__name__} error: No files found in {self.root_dir}"
            )

    def _fetch_schema(self, jsonschema_ref: str) -> dict:
        """Fetch a schema from a URL and cache it in the requests cache"""
        try:
            self.schema_cache[jsonschema_ref] = self.schema_cache.get(
                jsonschema_ref
            ) or fetch_schema(jsonschema_ref)
            self._jsonschema_ref_to_validator[jsonschema_ref] = (
                self._jsonschema_ref_to_validator.get(jsonschema_ref)
                or jsonschema_validator_for(self.schema_cache[jsonschema_ref])
            )
        except requests.exceptions.RequestException as exc:
            error_message = f"Error fetching schema {jsonschema_ref}: {str(exc)}"
            raise ValidationError(error_message) from exc

        return self.schema_cache[jsonschema_ref]

    def validate_schema(self, file: str, content: Dict):
        """Validate the yaml file for schema adherence"""
        if "schema" not in content:
            raise ValidationError(f"Schema not found in {file}")

        jsonschema_ref = content["schema"]

        try:
            self._fetch_schema(jsonschema_ref)
        except ValidationError as exc:
            error_message = f"Validation error for {file}: \n{str(exc)}"
            raise ValidationError(error_message) from exc

        try:
            # might get rueyaml CommentedMap or CommentedSeq etc., which
            # doesnt play nice with the rust impl
            ensured_dict_content = convert_ruemelyaml_commentedmap_to_dict(content)
            self._jsonschema_ref_to_validator[jsonschema_ref].validate(
                ensured_dict_content
            )
        except JsonValidationError as exc:
            error_message = f"Validation error for {file}: \n{str(exc)}"
            raise ValidationError(error_message) from exc

    def _get_additional_metadata_from_generated(  # pylint: disable=unused-argument
        self, filepath: str
    ) -> Optional[Dict]:
        """Get additional metadata from the generated step"""
        return None

    @abstractmethod
    def _get_base_generated_files(self) -> Dict[str, Dict]:
        """
        Set Autoupdate templates in {file_path: content} format

        NOTE: unsafe to call this method directly, since if not checkout out
              to the correct commit, the output will be incorrect.
        """
        raise NotImplementedError

    @functools.cached_property
    def original_file_state(self) -> Dict[str, Dict]:
        """Collect the original file state"""
        return self._get_file_contents_for_suffix(self.SUFFIX)

    @functools.cached_property
    def generated_file_state(self) -> Dict[str, Dict]:
        """Collect the raw generated file state"""
        if (
            not self.MUST_GENERATE_EVEN_IF_ENTITY_TYPE_EXISTS
            and self.original_file_state
        ):
            # If the entity type exists in the original file state,
            # we don't want to generate a new file
            return self.original_file_state

        base_gen_files = self._get_base_generated_files()
        if self.schema_to_prune_generated:
            for file, content in base_gen_files.items():
                # does no validation, just prunes the additional properties.
                base_gen_files[file] = prune_additional_properties(
                    content, self.schema_to_prune_generated
                )
        return {
            self.config.assert_dapi_location_is_valid(file): base_content
            for file, base_content in base_gen_files.items()
        }

    @functools.cached_property
    def merged_file_state(self) -> Dict[str, Dict]:
        """Merge the original and raw generated file states"""
        original_file_state = self.original_file_state
        generated_file_state = self.generated_file_state

        merged_file_state = {}
        for file in self.total_filepaths:
            self.config.assert_dapi_location_is_valid(file)
            original_content = original_file_state.get(file)
            generated_content = generated_file_state.get(file)

            if original_content is None:
                merged_content = generated_content

            elif generated_content is None:
                merged_content = original_content

            else:
                merged_content = self.merge(generated_content, original_content)

            merged_file_state[file] = merged_content

        return merged_file_state

    def validate_content(self, file: str, content: Dict, fileset: FileSet):
        """Validate the content of the files"""

    @property
    def base_tags(self) -> Dict:
        """Get the base tags for the validator"""
        return {
            "validator_type": self.__class__.__name__,
            "org_name": self.config.org_name_snakecase,
        }

    def _collect_validation_errors(self, fileset: FileSet) -> List[str]:
        """Run the validators"""
        # Update the files after autoupdate
        # NOTE: think about if we want to use the minimal schema to validate
        #       here as well. Since dapi server does this, and since in
        #       the future we may want to validate after features run,
        #       we omit this for now.

        # Check if the files exist if enforce_existence is True
        if self.enforce_existence_at:
            self.validate_existance_at()

        file_to_content = self.get_file_state(fileset)

        # Collect the errors for all the files
        errors = []
        for file, content in file_to_content.items():
            try:
                self.validate_schema(file, content)
            except ValidationError as exc:
                errors.append(str(exc))
            else:
                try:
                    self.validate_content(file, content, fileset)
                except ValidationError as exc:
                    commit = self.commit_sha or "CURRENT_STATE"
                    errors.append(f"{commit} {fileset.value}: {str(exc)}")

        # Increment the counter for the number of items validated
        tags = {
            **self.base_tags,
            "fileset": fileset.value,
        }
        increment_counter(
            LogCounterKey.VALIDATOR_ITEMS,
            value=len(file_to_content),
            tags=tags,
        )
        return errors

    @functools.cached_property
    def _validation_errors(self) -> List[MultiValidationError]:
        """
        All of the validation errors
        """
        errors = self._collect_validation_errors(FileSet.ORIGINAL)
        errors.extend(self._collect_validation_errors(FileSet.GENERATED))
        errors.extend(self._collect_validation_errors(FileSet.MERGED))
        return errors

    def validate(self):
        """Validate the files"""
        errors = self._validation_errors
        if errors:
            # Increment the counter for the number of errors
            increment_counter(
                LogCounterKey.VALIDATOR_ERRORS,
                value=len(errors),
                tags=self.base_tags,
            )
            raise MultiValidationError(
                errors, f"OpenDAPI {self.__class__.__name__} error"
            )

    def get_validated_files(self) -> Dict[str, CollectedFile]:
        """Validate and return files"""
        self.validate()
        return self.collected_files

    @property
    def total_filepaths(self) -> Set[str]:
        """Get the total filepaths"""
        return self.original_file_state.keys() | self.generated_file_state.keys()

    @functools.cached_property
    def collected_files(self) -> Dict[str, CollectedFile]:
        """Return collected files"""
        return {
            file: CollectedFile(
                original=self.original_file_state.get(file),
                generated=self.generated_file_state.get(file),
                merged=self.merged_file_state[file],
                filepath=file,
                commit_sha=self.commit_sha,
                entity=self.ENTITY,
                root_dir=self.root_dir,
                additional_metadata_from_generated=self._get_additional_metadata_from_generated(
                    file
                ),
            )
            for file in self.total_filepaths
        }

    @staticmethod
    def _organize(
        results: List[CollectedFile],
    ) -> Dict[OpenDAPIEntity, Dict[str, CollectedFile]]:
        """Organize the results"""
        organized_results = defaultdict(dict)
        for result in results:
            if result.filepath in organized_results[result.entity]:
                # NOTE: we have seen this happen if the HEAD ORIGINAL is missing context -
                #       so it goes to fallback validator, but then when we run the other validators
                #       that pick up on the actual model it creates another dapi for HEAD GENERATED
                #       for that validator.
                raise ValueError(
                    f"Multiple results for {result.filepath} in {result.entity}."
                    "This generally happens if the same file is processed by multiple validators, "
                    "which in turn generally happens if the committed file is missing integration "
                    "info in the context section, which is usually user error. Delete the m"
                )
            organized_results[result.entity][result.filepath] = result
        return organized_results

    @classmethod
    def run_validators(  # pylint: disable=too-many-arguments, too-many-locals
        cls,
        validators: Iterable[Type[BaseValidator]],
        root_dir: str,
        runtime: str,
        change_trigger_event: ChangeTriggerEvent,
        commit_type: CommitType,
        enforce_existence_at: Optional[FileSet] = None,
        override_config: Optional[OpenDAPIConfig] = None,
        minimal_schemas: Optional[Schemas] = None,
        commit_already_checked_out: bool = False,
        # integration specific flags
        runtime_skip_generation: bool = False,
        dbt_skip_generation: bool = False,
    ) -> Tuple[
        Dict[OpenDAPIEntity, Dict[str, CollectedFile]], List[MultiValidationError]
    ]:
        """
        Run the validators, returning an output organized by entity, and sanity checking that
        there are no duplicate filepaths across entities.
        """
        collected_files = []
        errors = []
        with _maybe_git_commit_stash(
            root_dir, commit_already_checked_out, commit_type, change_trigger_event
        ):
            for validator in validators:
                kwargs = {
                    "root_dir": root_dir,
                    "runtime": runtime,
                    "enforce_existence_at": enforce_existence_at,
                    "override_config": override_config,
                    "schema_to_prune_generated": (
                        minimal_schemas.minimal_schema_for(validator)
                        if minimal_schemas
                        else None
                    ),
                    "change_trigger_event": change_trigger_event,
                    "commit_type": commit_type,
                }

                if validator.INTEGRATION_TYPE is IntegrationType.RUNTIME:
                    kwargs["skip_generation"] = runtime_skip_generation
                elif validator.INTEGRATION_TYPE is IntegrationType.DBT:
                    kwargs["skip_generation"] = dbt_skip_generation

                inst = validator(**kwargs)
                try:
                    collected_files.extend(inst.get_validated_files().values())
                except MultiValidationError as e:
                    errors.append(e)

            return cls._organize(collected_files), errors
