from typing import *

import datahold

from preparse.core.enums import *
from preparse.core.warnings import *

__all__ = ["Optdict"]


class Optdict(datahold.OkayDict):
    @property
    def data(self: Self) -> dict:
        return dict(self._data)

    @data.setter
    def data(self: Self, value: Any) -> None:
        d: dict
        d = dict(value)
        d = dict(zip(map(str, d.keys()), map(Nargs, d.values()), strict=True))
        self._data = d
