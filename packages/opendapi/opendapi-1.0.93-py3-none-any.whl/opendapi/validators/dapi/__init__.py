"""Validators for DAPI."""

# pylint: disable=unused-import

from .activerecord import ActiveRecordDapiValidator
from .alembic import AlembicDapiValidator
from .base.main import BaseDapiValidator, DapiValidator, ORMIntegration
from .dbt import DbtDapiValidator
from .fallback import FallbackDapiValidator
from .liquibase import LiquibaseDapiValidator
from .prisma import PrismaDapiValidator
from .protobuf import ProtobufDapiValidator
from .pyiceberg import PyIcebergDapiValidator
from .pynamodb import PynamodbDapiValidator
from .sequelize import SequelizeDapiValidator
from .sqlalchemy import SqlAlchemyDapiValidator
from .typeorm import TypeOrmDapiValidator

get_validator_for_integration = BaseDapiValidator.get_validator


ALWAYS_RUN_DAPI_VALIDATORS = {
    FallbackDapiValidator,
}
