"""Type helpers for ``cg_maybe``."""

import sys
import typing as t

if sys.version_info >= (3, 8):
    from typing import Final as Final
    from typing import Literal as Literal
    from typing import Protocol as Protocol
else:  # pragma: no cover
    from typing_extensions import (
        Final as Final,
    )
    from typing_extensions import (
        Literal as Literal,
    )
    from typing_extensions import (
        Protocol as Protocol,
    )

_T = t.TypeVar('_T', covariant=True)
_TT = t.TypeVar('_TT')


class SupportsLessThan(Protocol[_T]):
    """A type that supports the `<` operator."""

    def __lt__(self: _TT, other: _TT) -> bool: ...


class SupportsGreaterOrEqual(Protocol[_T]):
    """A type that supports the `>=` operator."""

    def __ge__(self: _TT, other: _TT) -> bool: ...
