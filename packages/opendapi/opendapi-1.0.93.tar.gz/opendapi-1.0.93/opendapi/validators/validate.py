"""Module for running Validators"""

import functools
from typing import Dict, List, Optional, Tuple, Type

from opendapi.adapters.git import ChangeTriggerEvent
from opendapi.cli.common import Schemas, print_cli_output
from opendapi.config import OpenDAPIConfig
from opendapi.defs import CommitType, OpenDAPIEntity
from opendapi.logging import LogDistKey, Timer
from opendapi.validators.base import BaseValidator
from opendapi.validators.categories import CategoriesValidator
from opendapi.validators.dapi import (
    ALWAYS_RUN_DAPI_VALIDATORS,
    ORMIntegration,
    get_validator_for_integration,
)
from opendapi.validators.datastores import DatastoresValidator
from opendapi.validators.defs import CollectedFile, FileSet, MultiValidationError
from opendapi.validators.dummy_opendapi_config import DummyOpendapiConfigValidator
from opendapi.validators.purposes import PurposesValidator
from opendapi.validators.subjects import SubjectsValidator
from opendapi.validators.teams import TeamsValidator


@functools.lru_cache(maxsize=8)
def collect_and_validate_cached(  # pylint: disable=too-many-arguments
    opendapi_config: OpenDAPIConfig,
    minimal_schemas: Schemas,
    runtime: str,
    change_trigger_event: ChangeTriggerEvent,
    commit_type: CommitType,
    enforce_existence_at: Optional[FileSet] = None,
    commit_already_checked_out: bool = False,
    # integration specific flags
    runtime_skip_generation: bool = False,
    dbt_skip_generation: bool = False,
) -> Tuple[Dict[OpenDAPIEntity, Dict[str, CollectedFile]], List[MultiValidationError]]:
    """
    Accumulate DAPI files and metadata for integrations specified in the
    OpenDAPI configuration file.

    For certain integrations such as DBT and PynamoDB, this command will also run
    additional commands in the respective integration directories to generate DAPI files.
    """

    commit_txt = change_trigger_event.commit_type_to_sha(commit_type)
    print_cli_output(
        (
            f"Accumulating DAPI metadata for {commit_txt} for the integrations defined in "
            "`opendapi.config.yaml` configuration."
        ),
        color="green",
    )

    # determine all of the required validators
    validators: List[Type[BaseValidator]] = [
        CategoriesValidator,
        DatastoresValidator,
        PurposesValidator,
        SubjectsValidator,
        TeamsValidator,
        DummyOpendapiConfigValidator,
        *ALWAYS_RUN_DAPI_VALIDATORS,
    ]

    print_cli_output(
        "Identifying your integrations...",
        color="yellow",
    )

    for intg in ORMIntegration.integrations():
        if opendapi_config.has_integration(intg, runtime):
            validators.append(get_validator_for_integration(intg))
            print_cli_output(f"  Found {intg.value}...", color="green")

    print_cli_output(
        "Accumulating DAPI file metadata for your integrations...",
        color="yellow",
    )
    metrics_tags = {"org_name": opendapi_config.org_name_snakecase}
    with Timer(dist_key=LogDistKey.VALIDATE_AND_COLLECT, tags=metrics_tags):
        collected_files, errors = BaseValidator.run_validators(
            validators=validators,
            root_dir=opendapi_config.root_dir,
            runtime=runtime,
            change_trigger_event=change_trigger_event,
            commit_type=commit_type,
            enforce_existence_at=enforce_existence_at,
            # may not exist at base commit
            override_config=opendapi_config,
            minimal_schemas=minimal_schemas,
            commit_already_checked_out=commit_already_checked_out,
            # integration specific flags
            runtime_skip_generation=runtime_skip_generation,
            dbt_skip_generation=dbt_skip_generation,
        )

    print_cli_output(
        "Finished.",
        color="green",
    )
    return collected_files, errors
