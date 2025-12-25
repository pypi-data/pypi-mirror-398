import sys
from typing import *

from preparse._processing.items import *

__all__ = ["pull"]


def pull(args: Optional[Iterable] = None) -> list[Positional]:
    "This method parses args."
    argiter: Iterable
    if args is None:
        argiter = sys.argv[1:]
    else:
        argiter = args
    return list(map(Positional, argiter))
