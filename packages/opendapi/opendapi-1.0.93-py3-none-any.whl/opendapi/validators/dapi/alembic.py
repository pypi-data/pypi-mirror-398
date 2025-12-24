"""Alembic DAPI validator module"""

import os
import subprocess  # nosec: B404
from dataclasses import dataclass
from typing import Type

from opendapi.defs import ORMIntegration
from opendapi.logging import logger
from opendapi.validators.dapi.base.ddl import DdlBasedDapiValidator, DdlBasedProjectInfo


@dataclass
class AlembicProjectInfo(DdlBasedProjectInfo):
    """Data class for an alembic project information"""

    integration: ORMIntegration = ORMIntegration.ALEMBIC

    # Alembic and Liquibase have auditing tables that we don't need to generate DAPIs for
    AUDITING_TABLE_NAMES = ["alembic_version"]

    def _get_ddl(self) -> str:
        """
        Get the DDL from the alembic migrations.

        Alembic/sqlalchemy versions are filled with gotchas.
        So, we will expect the customer CI runtime to have
        the right library versions installed.

        This must be run in the alembic directory
        """
        try:
            result = subprocess.run(
                ["alembic", "upgrade", "head", "--sql"],
                capture_output=True,
                text=True,
                check=True,
                cwd=os.path.dirname(self.artifact_full_path),
            )  # nosec
        except subprocess.CalledProcessError as e:  # pragma: no cover
            logger.info(e.stderr)
            logger.info(e.stdout)
            raise e
        return result.stdout


class AlembicDapiValidator(DdlBasedDapiValidator[AlembicProjectInfo]):
    """
    Validator class for DAPI files created for Alembic datasets
    """

    INTEGRATION_NAME: ORMIntegration = ORMIntegration.ALEMBIC
    DEFAULT_ARTIFACT_PATH = "alembic.ini"
    PROJECT_INFO_TYPE: Type[AlembicProjectInfo] = AlembicProjectInfo
