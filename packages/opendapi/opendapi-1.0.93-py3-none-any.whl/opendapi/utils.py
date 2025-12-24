"""Utility functions for the OpenDAPI client."""

# pylint: disable=unnecessary-lambda-assignment

import asyncio
import base64
import io
import json
import os
import re
import sys
from copy import deepcopy
from functools import cmp_to_key, lru_cache
from importlib.metadata import version
from json import JSONDecodeError
from json import dump as json_dump
from json import dumps as json_dumps
from json import load as json_load
from json import loads as json_loads
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    TextIO,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from urllib.parse import urlparse

import jsonref
import requests
import requests_cache
import urllib3
from jsonschema import validators
from jsonschema.validators import validator_for
from requests.adapters import HTTPAdapter
from ruamel.yaml import YAML as _YAML
from ruamel.yaml import CommentedMap
from ruamel.yaml.error import YAMLError
from urllib3.util.retry import Retry

from opendapi.defs import DAPI_ORM_EXTRACTED_FIELDS_SCHEMA, OPENDAPI_DOMAIN, HTTPMethod
from opendapi.feature_flags import FeatureFlag, get_feature_flag
from opendapi.logging import logger

T = TypeVar("T")


@lru_cache(maxsize=1)
def get_schema_session() -> requests.Session:
    """
    Get a session for fetching schemas
    Create when needed to avoid stale connections
    """
    return create_session_with_retries(
        cached_session_name="opendapi_schema_cache",
        total_retries=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
    )


@lru_cache(maxsize=128)
def _load_local_schema(local_spec_path: str) -> Optional[dict]:
    """
    Load a schema from a local file path with caching.

    Caches the parsed JSON to avoid repeated file I/O for the same schema.
    Since bundled specs don't change at runtime, this cache is safe and efficient.

    Args:
        local_spec_path: Path to the local schema file

    Returns:
        Parsed schema dict if file exists and is valid, None otherwise
    """
    if not os.path.exists(local_spec_path):
        return None

    try:
        with open(local_spec_path, "r", encoding="utf-8") as f:
            return json_load(f)
    except (OSError, JSONDecodeError) as exc:
        # If local file read fails, log and return None to trigger fallback
        logger.debug(
            "Failed to load local schema from %s: %s. Falling back to remote.",
            local_spec_path,
            exc,
        )
        return None


def convert_ruemelyaml_commentedmap_to_dict(content: Union[CommentedMap, dict]) -> dict:
    """
    Convert a ruemly yaml CommentedMap to a dict

    NOTE: this is a workaround to get the rust to work with ruemelyaml internals, since they all subclass
          their respective json-compatible types, so it works in pure python, but doesnt play nice with rust.
          json.dumps works since CommentedMap, CommentedSeq, ScalarNode, etc. all subclass their respective
          json-compatible types, so we can just dump and load to get a dict

    NOTE: merging may result in dicts that internally have CommentedMap or CommentedSeq,
          so we do not do isinstance checks as performance optimizations before, since
          checking exhaustively requires recursing the entire structure, which isnt worth
    """
    return json.loads(json.dumps(content))


class YAML(_YAML):
    """YAML class for OpenDAPI"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable aliasing
        self.representer.ignore_aliases = lambda *_: True


def dump_dict_to_yaml_str(content: dict, yaml: Optional[YAML] = None) -> str:
    """
    Dumps a dictionary to a yaml string
    """
    str_io = io.StringIO()
    yaml = yaml or YAML()
    yaml.dump(content, str_io)
    return str_io.getvalue()


def make_snake_case(string: str) -> str:
    """Convert a string to snake case"""
    return re.sub(r"[\s\-\.]+", "_", string).lower()


def read_yaml_or_json(filepath: str, yaml: YAML = None) -> dict:
    """Read a yaml or json file"""
    yaml = yaml or YAML()
    with open(filepath, "r", encoding="utf-8") as filepath_handle:
        try:
            if filepath.endswith(".yaml") or filepath.endswith(".yml"):
                return yaml.load(filepath_handle.read())
            if filepath.endswith(".json"):
                return json_load(filepath_handle)
        except (JSONDecodeError, YAMLError) as exc:
            raise ValueError(f"Error parsing {filepath}: {exc}") from exc
    raise ValueError(f"Unsupported filepath type for {filepath}")


def _write_to_io(
    filepath: str, data: dict, io_: TextIO, yaml: YAML, json_spec: Optional[dict] = None
) -> None:
    """Write a dict as yaml or json file format to the io object"""
    if filepath.endswith(".yaml") or filepath.endswith(".yml"):
        # this mutates the data, so we deepcopy it
        sorted_yaml_dump(deepcopy(data), io_, json_spec=json_spec, yaml=yaml)
    elif filepath.endswith(".json"):
        json_dump(data, io_, indent=4)
    else:
        raise ValueError(f"Unsupported filepath type for {filepath}")


def write_to_yaml_or_json_string(
    filepath: str,
    data: dict,
    yaml: YAML = None,
    json_spec: Optional[dict] = None,
) -> str:
    """Write a dict to a yaml or json - formatted string"""
    yaml = yaml or YAML()
    sio = io.StringIO()
    _write_to_io(filepath, data, sio, yaml, json_spec)
    return sio.getvalue()


def write_to_yaml_or_json(
    filepath: str,
    data: dict,
    yaml: YAML = None,
    json_spec: Optional[dict] = None,
) -> None:
    """Write a dict to a yaml or json file"""
    yaml = yaml or YAML()
    with open(filepath, "w", encoding="utf-8") as filepath_handle:
        _write_to_io(filepath, data, filepath_handle, yaml, json_spec=json_spec)


def get_repo_name_from_root_dir(root_dir: str) -> str:
    """Get the repo name from the root directory"""
    return os.path.basename(root_dir.rstrip("/"))


def fetch_schema(schema_url: str) -> dict:
    """
    Fetch a schema from a URL, checking local bundled specs first.

    First attempts to load the schema from the bundled specs in the package.
    If the local file doesn't exist or the version is not available locally,
    falls back to fetching from the remote URL.
    """
    schema_url = (
        schema_url.replace(OPENDAPI_DOMAIN, "next.opendapi.org")
        if get_feature_flag(FeatureFlag.USE_NEXT_OPENDAPI_ORG_PROXY)
        else schema_url
    )
    parsed_url = urlparse(schema_url)
    if not parsed_url.netloc.endswith(OPENDAPI_DOMAIN):
        raise ValueError(
            f"Unsupported schema found at {schema_url} - must use {OPENDAPI_DOMAIN}"
        )

    # Try to load from local bundled specs first
    # URL format: https://opendapi.org/spec/{version}/{filename}.json
    path_parts = parsed_url.path.strip("/").split("/")
    if len(path_parts) >= 3 and path_parts[0] == "spec":
        spec_path = os.path.join(*path_parts[1:])

        # Get the package directory
        package_dir = os.path.dirname(os.path.abspath(__file__))
        local_spec_path = os.path.join(package_dir, "specs", spec_path)

        # Try to load from cached local file (avoids repeated file I/O)
        local_schema = _load_local_schema(local_spec_path)
        if local_schema is not None:
            return local_schema

    # Fallback to remote fetch
    return get_schema_session().get(schema_url, timeout=(10, 10)).json()


def sorted_yaml_dump(
    content: dict,
    stream: TextIO,
    json_spec: Optional[dict] = None,
    yaml: YAML = None,
):
    """Dump a yaml file with sorted keys, as indicated by the json schema (or alphabetically)"""
    yaml = yaml or YAML()

    if not json_spec:
        jsonschema_ref = content.get("schema")
        json_spec = fetch_schema(jsonschema_ref) if jsonschema_ref else {}

    def _rec_sort(item, schema):
        """Helper function to recursively sort a dict"""

        # We will use the priority in the schema to sort the keys.
        # If priority is not present, we will use a high number to sort it at the end.
        # If priority is the same, we will sort the keys alphabetically.
        sorter = lambda x: (schema.get(x, {}).get("order", 99999), x)

        if isinstance(item, dict):
            # could use dict in newer python versions
            res = CommentedMap()
            schema = schema.get("properties", {})
            for k in sorted(item.keys(), key=sorter):
                res[k] = _rec_sort(item[k], schema.get(k, {}))
            return res

        if isinstance(item, list):
            schema = schema.get("items", {})
            for idx, elem in enumerate(item):
                item[idx] = _rec_sort(elem, schema)

        return item

    json_spec = jsonref.JsonRef.replace_refs(json_spec)
    sorted_content = _rec_sort(content, json_spec)
    yaml.dump(sorted_content, stream)


def make_api_w_query_and_body(
    url: str,
    headers: Dict,
    query_params: Optional[Dict],
    body_json: Optional[Dict],
    method: HTTPMethod,
    timeout: int = 30,
    req_session: Optional[requests.Session] = None,
) -> Tuple[requests.Response, Optional[requests.Session]]:
    """Make API calls to github, returning entire response"""
    request_maker = req_session or requests

    if method is HTTPMethod.POST:
        response = request_maker.post(
            url,
            headers=headers,
            params=query_params,
            json=body_json,
            timeout=timeout,
        )
        return response, req_session
    if method is HTTPMethod.GET:
        if body_json:
            raise ValueError("GET requests cannot have a body")
        response = request_maker.get(
            url,
            params=query_params,
            headers=headers,
            timeout=timeout,
        )
        return response, req_session

    raise ValueError(f"Unsupported method: {method}")  # pragma: no cover


def _remove_additional_properties_validator(base_validator_cls):
    """
    Extend a validator to remove additional properties not found in the schema.
    Edited from
    https://stackoverflow.com/questions/44694835/remove-properties-from-json-object-not-present-in-schema

    NOTE: Does not work with separate-schema polymorphism,
    since we do not fetch the other schema
    """

    original_properties_validator = base_validator_cls.VALIDATORS["properties"]

    def remove_additional_properties(validator, properties, instance, schema):
        """
        Callback invoked by jsonschema to validate a properties present in an instance
        against the expected properties [properties] defined in the schema.

        This callback removes any additional properties found in the instance
        that are not found in the schema.
        """
        if not validator.is_type(instance, "object"):
            return

        for prop in list(instance.keys()):
            if prop not in properties:
                del instance[prop]

        yield from original_properties_validator(
            validator, properties, instance, schema
        )

    return validators.extend(
        base_validator_cls,
        {
            **base_validator_cls.VALIDATORS,
            "properties": remove_additional_properties,
        },
    )


def prune_additional_properties(inst: dict, schema: dict) -> dict:
    """
    Trim the inst of additional properties not found in the schema

    NOTE: This does not validate the instance, only prunes it, and does not
          work with separate-schema polymorphism, since we do not fetch the other schema
    """
    inst = deepcopy(inst)
    validator_for_schema = validator_for(schema)
    remove_additional_cls = _remove_additional_properties_validator(
        validator_for_schema
    )
    # iterates through all of the errors - meaning that the entire schema is traversed,
    # allowing us to prune nested objects as well
    # Note that we never raise the error, since this does not validate, only prunes
    for _ in remove_additional_cls(schema).iter_errors(inst):
        pass
    return inst


def encode_json_to_base64(json_data: Any) -> str:
    """Encode json to a base64 string"""
    return base64.b64encode(json_dumps(json_data).encode("utf-8")).decode("utf-8")


def decode_base64_to_json(base64_str: str) -> Any:
    """Decode a base64 string to json"""
    return json_loads(base64.b64decode(base64_str.encode("utf-8")).decode("utf-8"))


def sort_dapi_fields(fields: List[Dict]) -> List[Dict]:
    """
    Sort the fields of a dapi

    NOTE: this may run BEFORE schema validation, so we should not assume
          anything about the elements that are present within the fields
    """

    def _cmp(field_one: dict, field_two: dict) -> int:
        """
        Compare two fields

        most of the time comparing the name is enough, but we may have duplicates
        in legacy dapis, and so we have a fallback to compare the entire field
        """
        # if fields are missing name, they will fail schema validation,
        # and the sorted order is not important (nor would we know how to sort it)
        f1_name = field_one.get("name")
        f2_name = field_two.get("name")
        f1_val, f2_val = (
            (
                json.dumps(field_one, sort_keys=True),
                json.dumps(field_two, sort_keys=True),
            )
            if f1_name == f2_name
            else (f1_name, f2_name)
        )
        if f1_val == f2_val:
            return 0
        return 1 if f1_val > f2_val else -1

    return sorted(fields, key=cmp_to_key(_cmp))


def has_underlying_model_changed(
    dapi_one: Optional[Dict],
    dapi_two: Optional[Dict],
    sort_fields: bool = False,
) -> bool:
    """
    Check if the underlying model has changed.

    This is done by pruning all non-ORM-derived portions from the Dapis and comparing them.

    NOTE: generally, setting sort_fields to False should already be done if they are already
          sorted as a performance optimization, but this is the default since the validator
          already
    """
    dapi_one_copy = (dapi_one or {}).copy()
    dapi_two_copy = (dapi_two or {}).copy()
    if sort_fields:
        dapi_one_copy["fields"] = sort_dapi_fields(dapi_one_copy.get("fields", []))
        dapi_two_copy["fields"] = sort_dapi_fields(dapi_two_copy.get("fields", []))

    # most of the time, the dapis are equal, and there therefore is no need to prune,
    # so lets only use pruning as a fallback
    return dapi_one_copy != dapi_two_copy and prune_additional_properties(
        dapi_one_copy, DAPI_ORM_EXTRACTED_FIELDS_SCHEMA
    ) != prune_additional_properties(dapi_two_copy, DAPI_ORM_EXTRACTED_FIELDS_SCHEMA)


def has_dapi_file_materially_changed(
    dapi_one: Optional[Dict],
    dapi_two: Optional[Dict],
    sort_fields: bool = False,
) -> bool:
    """
    Check if the dapi file has materially changed.

    NOTE: generally, setting sort_fields to False should already be done if they are already
          sorted as a performance optimization

    NOTE: this is somewhat superflous, since we sort the fields at generation time,
          but in case that paradigm changes or the inputs come from elsewhere,
          we introduce this
    """
    dapi_one_copy = (dapi_one or {}).copy()
    dapi_two_copy = (dapi_two or {}).copy()
    if sort_fields:
        dapi_one_copy["fields"] = sort_dapi_fields(dapi_one_copy.get("fields", []))
        dapi_two_copy["fields"] = sort_dapi_fields(dapi_two_copy.get("fields", []))
    return dapi_one_copy != dapi_two_copy


def build_location_without_repo_from_fullpath(root_dir: str, fullpath: str):
    """
    Build a full path from the qualified location.

    full path is root_dir/path/to/file
    example:
    root_dir = /tmp/repo
    fullpath = /tmp/repo/path/to/file
    return path/to/file
    """
    return re.sub(root_dir, "", fullpath).lstrip("/")


class StdOutRetry(Retry):
    """Retry that prints the request and response to stdout"""

    def increment(
        self,
        method=None,
        url=None,
        response=None,
        error=None,
        _pool=None,
        _stacktrace=None,
    ):  # pragma: no cover
        log = "\n\n!!A method is being retried!!"
        if response:
            if isinstance(response, requests.Response):
                log += f"\nResponse: {response.url} {response.status_code}"
            elif isinstance(response, urllib3.HTTPResponse):
                log += f"\nResponse: {response.url} {response.status}"
        log += "\n\n"
        # NOTE: configured to go to stdout as well as logs
        logger.info(log)
        sys.stdout.flush()
        return super().increment(method, url, response, error, _pool, _stacktrace)


def create_session_with_retries(
    total_retries: int = 1,
    backoff_factor: int = 1,
    status_forcelist: Optional[List[int]] = None,
    allowed_methods: Optional[List[str]] = None,
    cached_session_name: Optional[str] = None,
    print_retries: bool = False,
) -> requests.Session:
    """Create a session with retries."""
    req_session = (
        requests_cache.CachedSession(
            cached_session_name,
            expire_after=300,
            backend="memory",
        )
        if cached_session_name
        else requests.Session()
    )
    # Add retry once after 60s for 500, 502, 503, 504
    # This is to handle the case where the server is starting up
    # or when any AI per-minute token limits are hit
    status_forcelist = status_forcelist or [429, 500, 502, 503, 504]
    allowed_methods = allowed_methods or ["POST", "GET", "HEAD"]

    kwargs = {
        "total": total_retries,
        "connect": total_retries,
        "read": total_retries,
        "status": total_retries,
        "backoff_factor": backoff_factor,
        "status_forcelist": status_forcelist,
        "allowed_methods": set(allowed_methods),
        "respect_retry_after_header": True,
    }

    # Add some more options for urllib3 2.0.0 and above
    urllib3_version = version("urllib3").split(".")
    if int(urllib3_version[0]) >= 2:  # pragma: no cover
        kwargs.update(
            {
                "backoff_jitter": 0.5,
                "backoff_max": 120,  # Default is 120
            }
        )

    retries = StdOutRetry(**kwargs) if print_retries else Retry(**kwargs)
    adapter = HTTPAdapter(max_retries=retries)
    req_session.mount("http://", adapter)
    req_session.mount("https://", adapter)
    return req_session


async def async_backoff_retry(
    func: Callable[[], Awaitable[T]],
    max_attempts: int = 3,
    initial_backoff_seconds: int = 1,
    exceptions_to_catch: Tuple[Type[Exception], ...] = (Exception,),
    exceptions_to_raise: Tuple[Type[Exception], ...] = tuple(),
) -> T:
    """
    Retry a function with exponential backoff
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return await func()
        except exceptions_to_catch as e:
            if attempt >= max_attempts or isinstance(e, exceptions_to_raise):
                raise
            backoff = initial_backoff_seconds * (2 ** (attempt - 1))
            await asyncio.sleep(backoff)
