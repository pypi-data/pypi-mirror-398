"""This module defines some util function for ``cg_request_args``.

It should not be used outside the ``cg_request_args`` module.
"""

import sys
import typing as t

try:
    from cg_helpers import readable_join
except ImportError:  # pragma: no cover

    def readable_join(lst: t.Sequence[str]) -> str:
        """Simple implementation of ``readable_join``."""
        return ', '.join(lst)


if sys.version_info >= (3, 9):
    from typing import Annotated as Annotated
else:  # pragma: no cover
    from typing_extensions import Annotated as Annotated

if sys.version_info >= (3, 8):
    from typing import (
        Final as Final,
    )
    from typing import (
        Literal as Literal,
    )
    from typing import (
        Protocol as Protocol,
    )
    from typing import (
        TypedDict as TypedDict,
    )
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
    from typing_extensions import (
        TypedDict as TypedDict,
    )


def _issubclass(value: t.Any, cls: t.Type) -> bool:
    return isinstance(value, type) and issubclass(value, cls)


def is_typeddict(value: object) -> bool:
    """Check if the given value is a TypedDict."""
    return _issubclass(value, dict) and hasattr(value, '__total__')


_TYPE_NAME_LOOKUP = {
    str: 'str',
    float: 'float',
    bool: 'bool',
    int: 'int',
    dict: 'mapping',
    list: 'list',
    type(None): 'null',
}


def type_to_name(typ: t.Type) -> str:
    """Convert the given type to a string."""
    if typ in _TYPE_NAME_LOOKUP:
        return _TYPE_NAME_LOOKUP[typ]
    return str(typ)  # pragma: no cover


T_COV = t.TypeVar('T_COV', covariant=True)
T = t.TypeVar('T')
Y = t.TypeVar('Y')
