"""Feature flags for the OpenDAPI client."""

import os
from enum import Enum
from typing import Dict


class FeatureFlag(Enum):
    """Feature flags for the OpenDAPI client."""

    USE_NEXT_OPENDAPI_ORG_PROXY = "use_next_opendapi_org_proxy"

    @property
    def to_env_var(self):
        """Convert the feature flag to an environment variable."""
        return f"FF_{self.value}"

    @classmethod
    def has_value(cls, value: str) -> bool:
        """Check if the feature flag has a value."""
        return any(value == item.value for item in cls)


def set_feature_flags(
    feature_flags: Dict[FeatureFlag, bool],
):
    """
    Set the feature flags for the OpenDAPI client.
    """

    for flag, value in feature_flags.items():
        os.environ[flag.to_env_var] = str(value).lower()


def get_feature_flag(flag: FeatureFlag) -> bool:
    """
    Get the feature flag for the OpenDAPI client.
    """
    return os.environ.get(flag.to_env_var, "").lower() == "true"
