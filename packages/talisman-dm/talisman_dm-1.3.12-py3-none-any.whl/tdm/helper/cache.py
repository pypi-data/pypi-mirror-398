from typing import Any, Callable, Optional


def cache_result(key_param: Optional[str] = None, cache: Optional[dict] = None):
    if cache is None:
        cache = {}

    def wrap(f: Callable):
        def wrapper(*args, **kwargs) -> Any:
            if key_param is not None:
                key = kwargs[key_param]
            elif args:
                key = args[0]
            else:
                key = kwargs[next(iter(kwargs))]
            if key in cache:
                return cache[key]
            result = f(*args, **kwargs)
            cache[key] = result
            return result

        return wrapper

    return wrap
