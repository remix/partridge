from functools import lru_cache


def cached_property(func, maxsize=None):
    func = lru_cache(maxsize=maxsize)(func)
    func = property(func)
    return func
