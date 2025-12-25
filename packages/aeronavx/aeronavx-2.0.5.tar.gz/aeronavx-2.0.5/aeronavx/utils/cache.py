from functools import lru_cache, wraps
from typing import Any, Callable, TypeVar


T = TypeVar('T')


def simple_cache(maxsize: int = 128) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        return lru_cache(maxsize=maxsize)(func)
    return decorator


def memoize(func: Callable[..., T]) -> Callable[..., T]:
    cache: dict[tuple[Any, ...], T] = {}

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        cache_key = (args, tuple(sorted(kwargs.items())))
        if cache_key not in cache:
            cache[cache_key] = func(*args, **kwargs)
        return cache[cache_key]

    wrapper.cache_clear = lambda: cache.clear()
    wrapper.cache_info = lambda: f"Cache size: {len(cache)}"

    return wrapper
