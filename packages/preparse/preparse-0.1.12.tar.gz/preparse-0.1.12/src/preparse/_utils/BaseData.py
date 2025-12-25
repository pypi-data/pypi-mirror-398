from typing import *

from datarepr import datarepr

__all__ = ["BaseData"]


class BaseData:

    def __repr__(self: Self) -> str:
        "This magic method implements repr(self)."
        return datarepr(type(self).__name__, **self.todict())

    def copy(self: Self) -> Self:
        "This method returns a copy of the current instance."
        return type(self)(**self.todict())

    def todict(self: Self) -> dict:
        "This method returns a dict representing the current instance."
        ans: dict
        try:
            ans = self._data
        except AttributeError:
            self._data = dict()
            ans = dict()
        else:
            ans = dict(ans)
        return ans
