"""
Helpers for weakref
"""

import functools
import weakref
from typing import Callable


def weak_lru_cache(maxsize=128, typed=False) -> Callable:
    """
    LRU Cache with weak reference to self.
    Note that one is created per cls instead of one per instance.
    Sources from
    https://stackoverflow.com/questions/33672412/
    python-functools-lru-cache-with-instance-methods-release-object
    """

    def wrapper(func: Callable):

        @functools.lru_cache(maxsize, typed)
        def _func(_self, *args, **kwargs):
            return func(_self(), *args, **kwargs)

        @functools.wraps(func)
        def inner(self, *args, **kwargs):
            return _func(weakref.ref(self), *args, **kwargs)

        return inner

    return wrapper
