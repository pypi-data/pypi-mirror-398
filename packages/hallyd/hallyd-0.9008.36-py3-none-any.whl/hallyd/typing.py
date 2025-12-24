#  SPDX-FileCopyrightText: © 2023 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Typing.

See Python :code:`typing` and :py:code:`collections.abc`.
"""
from typing import *
from collections.abc import *


@runtime_checkable
class SupportsQualifiedName(Protocol):
    __module__: str
    __qualname__: str


CallableWithQualifiedName = Union[Callable, SupportsQualifiedName]  # TODO Union -> Intersection
