from __future__ import absolute_import

from typing import Optional
from .config import create_configure, Configure

__configure: Optional[Configure] = None


def get_configure() -> Configure:
    global __configure
    if not __configure:
        __configure = create_configure()
    return __configure


__all__ = [
    "get_configure",
    "Configure"
]
