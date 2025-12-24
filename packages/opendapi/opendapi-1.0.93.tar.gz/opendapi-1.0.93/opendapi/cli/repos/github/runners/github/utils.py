"""
Github repo github runner related utils
"""

from typing import Optional

_IGNORED_AUTHORS = {
    "dependabot[bot]",
    "renovate[bot]",
}


def is_ignored_author(user_login: Optional[str]) -> bool:
    """Check if the author is ignored"""
    return user_login in _IGNORED_AUTHORS
