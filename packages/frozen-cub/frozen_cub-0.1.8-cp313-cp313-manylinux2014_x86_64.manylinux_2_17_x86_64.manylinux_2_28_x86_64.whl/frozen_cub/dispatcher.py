"""A generalized dispatcher for data, using FP principles."""

from __future__ import annotations

from collections.abc import Callable, Sized
from functools import wraps
from typing import TYPE_CHECKING, Any, NamedTuple, ParamSpec, Protocol, TypeVar

from frozen_cub.frozen import freeze
from frozen_cub.lru_cache import LRUCache
from frozen_cub.utils import CacheKey, check_conditions, get_cache_key

if TYPE_CHECKING:
    from frozen_cub.frozen import FrozenDict

MISSING = object()


class SupportsBool(Protocol):
    """Protocol for return values providing a dedicated truthiness hook."""

    def __bool__(self) -> bool: ...


type SupportsTruthiness = SupportsBool | Sized
type TruthReturnedCall = Callable[..., SupportsTruthiness | bool]


class DispatchEntry(NamedTuple):
    """A dispatch entry mapping a condition to a handler."""

    conditions: tuple[TruthReturnedCall, ...]
    kwargs: FrozenDict


class Entry(NamedTuple):
    """An entry mapping a handler to its call and kwargs."""

    call: Callable
    kwargs: dict[str, Any]

    def execute(self, *args: Any, extra_kwargs: dict | None = None) -> Any:
        """Execute the handler with the given args and kwargs."""
        if extra_kwargs is not None:
            return self.call(*args, **{**self.kwargs, **extra_kwargs})
        return self.call(*args, **self.kwargs)


class Registry(dict[DispatchEntry, Callable]):
    """A registry mapping keys to handler functions."""


T = TypeVar("T")
P = ParamSpec("P")


class Dispatcher:
    """A dispatcher that maps a conditional function to a handler function.

    Multiple ways to use the dispatcher:
        1. By keyword argument (default):
           @dispatcher.dispatcher()
           def func(obj, ...):
               ...
           foo = func(obj="bar")  # Dispatches on 'obj' argument
        2. By positional argument:
           @dispatcher.dispatcher()
           def func(arg1, arg2, ...):
               ...
           foo = func("bar", arg2=...)  # Dispatches on first positional argument
    """

    def __init__(self, arg: str = "obj", capacity: int = 256) -> None:
        """Initialize the dispatcher with an empty registry.

        Args:
            arg: The name of the argument to dispatch on (default: "obj")
            capacity: The maximum size of the LRU cache for resolved handlers (default: 256)
        """
        self._arg_name: str = arg
        self._registry: Registry = Registry()
        self._cache: LRUCache[CacheKey, Entry] = LRUCache(capacity=capacity)

    def register(self, *conditions: TruthReturnedCall, **kws) -> Callable:
        """Register a handler function for the given conditions.

        Args:
            *conditions: Predicate callables that return a truthy value when the handler should fire
                These callables should accept a single argument and return a boolean-like value.
            **kws: Additional keyword arguments to pass to the handler function
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            self._cache.clear()
            entry = DispatchEntry(conditions=conditions, kwargs=freeze(kws))
            self._registry[entry] = func

            @wraps(func)
            def handle_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return func(*args, **kwargs)

            return handle_wrapper

        return decorator

    def dispatcher(self) -> Callable:
        """Decorator to dispatch the function based on registered conditions.

        We let the decorated function handle missing arguments so nothing crashes here.

        We cache the resolved handler for each unique argument type and value combination
        to speed up repeated calls with the same argument.
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @wraps(func)
            def dispatch_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                arg: Any = kwargs.get(self._arg_name, args[0] if args else MISSING)
                if arg is MISSING:
                    return func(*args, **kwargs)
                cache_key: CacheKey = get_cache_key(type(arg), freeze(arg))
                cached: Entry | None = self._cache.get(cache_key)
                if cached is not None:
                    if kwargs:
                        return cached.execute(*args, extra_kwargs=kwargs)
                    return cached.execute(*args)
                for entry, handler in self._registry.items():
                    if check_conditions(entry.conditions, arg):
                        e = Entry(handler, entry.kwargs)
                        self._cache.set(cache_key, e)
                        if kwargs:
                            return e.execute(*args, extra_kwargs=kwargs)
                        return e.execute(*args)
                return func(*args, **kwargs)

            return dispatch_wrapper

        return decorator
