"""Liquibase DAPI validator module"""

import os
import subprocess  # nosec: B404
import tempfile
from dataclasses import dataclass
from typing import Type

from opendapi.config import get_project_path_from_full_path
from opendapi.defs import ORMIntegration, SqlDialect
from opendapi.logging import logger
from opendapi.validators.dapi.base.ddl import DdlBasedDapiValidator, DdlBasedProjectInfo
from opendapi.validators.installers.liquibase import (
    build_update_sql_command,
    precache_installs_for_liquibase_if_necessary,
)


@dataclass
class LiquibaseProjectInfo(DdlBasedProjectInfo):
    """Data class for an liquibase project information"""

    integration: ORMIntegration = ORMIntegration.LIQUIBASE
    # Alembic and Liquibase have auditing tables that we don't need to generate DAPIs for
    AUDITING_TABLE_NAMES = ["DATABASECHANGELOG", "DATABASECHANGELOGLOCK"]

    MAP_DIALECT_TO_LIQUIBASE_DIALECT = {
        SqlDialect.POSTGRES: "postgresql",
    }

    def _get_ddl(self) -> str:
        """
        Get the DDL from the liquibase migrations.

        Liquibase is a Java based CLI. We will expect the customer CI runtime to have
        Java and liquibase installed.

        """
        artifact_dir = os.path.dirname(self.artifact_full_path)
        dialect_value = self.MAP_DIALECT_TO_LIQUIBASE_DIALECT.get(
            self.dialect, self.dialect.value
        )
        # Liquibase creates a auditing file called databasechangelog.csv
        # when the updateSQL command is run. Keeping that in the working directory
        # will mess up our git state - so we use a temporary file.
        with tempfile.TemporaryDirectory() as tmp_dir:
            audit_file = os.path.join(tmp_dir, "databasechangelog.csv")
            sql_file = os.path.join(tmp_dir, "update.sql")
            offline_url = (
                f"offline:{dialect_value}?"
                # we don't need the SQL statements related to DATABASECHANGELOG
                # as we are not interested in the audit trail
                f"outputLiquibaseSql=none&"
                f"changeLogFile={audit_file}"
            )
            # okay to call within threads as java/liquibase will be installed already
            command, env = build_update_sql_command(
                changelog_file_fullpath=self.artifact_full_path,
                search_dir_fullpath=artifact_dir,
                offline_url=offline_url,
                output_file_fullpath=sql_file,
            )
            try:
                subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True,
                    env=env,
                )  # nosec
            except subprocess.CalledProcessError as e:  # pragma: no cover
                logger.info(e.stderr)
                logger.info(e.stdout)
                raise e
            with open(sql_file, "r", encoding="utf-8") as f:
                sql_content = f.read()
        return sql_content

    @property
    def _java_project_path(self) -> str:
        """Get the path of the project."""
        if "src/main/resources" in self.full_path:
            return self.full_path.split("src/main/resources")[0].rstrip("/")
        return self.full_path

    @property
    def project_name(self) -> str:
        """Get the name of the project."""
        proj_path = get_project_path_from_full_path(
            self.root_path, self._java_project_path
        )
        return proj_path.strip("/").replace("/", ".")

    def construct_dapi_location(self, table_name: str) -> str:
        """Construct the location of the DAPI file within a project"""
        return f"{self._java_project_path}/dapis/{table_name}.dapi.yaml"


class LiquibaseDapiValidator(DdlBasedDapiValidator[LiquibaseProjectInfo]):
    """
    Validator class for DAPI files created for Liquibase datasets
    """

    INTEGRATION_NAME: ORMIntegration = ORMIntegration.LIQUIBASE
    DEFAULT_ARTIFACT_PATH = "db.changelog-master.yml"
    PROJECT_INFO_TYPE: Type[LiquibaseProjectInfo] = LiquibaseProjectInfo

    def __init__(self, *args, **kwargs):
        """Initialize the validator and check for required dependencies."""

        precache_installs_for_liquibase_if_necessary()

        super().__init__(*args, **kwargs)
