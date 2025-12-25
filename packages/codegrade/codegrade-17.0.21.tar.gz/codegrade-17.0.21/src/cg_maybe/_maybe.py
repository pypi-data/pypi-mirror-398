"""This module combines ``Just`` and ``Nothing`` into ``Maybe``."""

import typing as t

from ._just import Just
from ._nothing import _Nothing

_Nothing._set_doc()  # noqa: SLF001

_T = t.TypeVar('_T', covariant=True)

Maybe = t.Union[Just[_T], _Nothing[_T]]
