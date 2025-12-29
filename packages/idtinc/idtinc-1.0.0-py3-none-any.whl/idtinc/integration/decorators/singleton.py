import functools
from typing import Any, Callable, Dict, Type, TypeVar

T = TypeVar("T")

_INSTANCES: Dict[Type, Any] = {}


def singleton(cls: Type[T]) -> Callable[..., T]:

    @functools.wraps(cls)
    def decorator(*args, **kwargs) -> T:
        if cls not in _INSTANCES:
            _INSTANCES[cls] = cls(*args, **kwargs)

        return _INSTANCES[cls]

    return decorator


def reset_singleton(cls: Type[T]) -> None:
    if cls in _INSTANCES:
        del _INSTANCES[cls]


def get_singleton_instance(cls: Type[T]) -> T:
    if cls not in _INSTANCES:
        raise KeyError(f"Singleton instance of {cls.__name__} not initialized")

    return _INSTANCES[cls]


def has_singleton_instance(cls: Type[T]) -> bool:
    return cls in _INSTANCES
