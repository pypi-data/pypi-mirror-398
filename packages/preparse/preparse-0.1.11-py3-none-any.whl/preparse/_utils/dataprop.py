from typing import *

__all__ = ["dataprop"]


def dataprop(func: Callable) -> property:
    "This magic method implements calling the current instance."

    def fget(self: Self) -> Any:
        return self._data[func.__name__]

    def fset(self: Self, value: Any) -> None:
        self._data = getattr(self, "_data", dict())
        self._data[func.__name__] = func(self, value)

    kwargs: dict
    kwargs = dict()
    kwargs["doc"] = func.__doc__
    kwargs["fget"] = fget
    kwargs["fset"] = fset
    return property(**kwargs)
