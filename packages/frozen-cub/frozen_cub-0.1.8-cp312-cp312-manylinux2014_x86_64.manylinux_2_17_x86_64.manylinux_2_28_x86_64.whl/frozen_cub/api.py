"""Helper types and constants for frozen_cub package."""

from .dispatcher import Dispatcher
from .frozen import FrozenDict, freeze, is_primitive
from .utils import (
    CacheKey,
    HashableValues,
    check_conditions,
    filter_out_nones,
    get_cache_key,
    has_nested_dicts,
    none_to_null,
    null_to_none,
)

NOT_CACHABLE = HashableValues(values=[None], cacheable=False)

type FreezableTypes = dict | list | set
type ThawTypes = FrozenDict | tuple | frozenset

__all__ = [
    "NOT_CACHABLE",
    "CacheKey",
    "Dispatcher",
    "FreezableTypes",
    "FrozenDict",
    "HashableValues",
    "ThawTypes",
    "check_conditions",
    "filter_out_nones",
    "freeze",
    "get_cache_key",
    "has_nested_dicts",
    "is_primitive",
    "none_to_null",
    "null_to_none",
]
