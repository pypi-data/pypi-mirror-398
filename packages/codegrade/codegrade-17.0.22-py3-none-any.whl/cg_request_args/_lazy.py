"""
This module contains a parser that makes it possible to lazily construct
another parser.
"""

import threading
import typing as t

from ._base import Parser
from ._swagger_utils import OpenAPISchema
from ._utils import T as _T

__all__ = ('Lazy',)


class Lazy(t.Generic[_T], Parser[_T]):
    """A wrapping parser that allows you to construct circular parsers.

    The method ``make_parser`` will be executed when you first try to parse
    something. It will only be executed once.
    """

    #: The lock to create new parsers with, this is a class variable to reduce
    #: memory pressure.
    _LOCK: t.ClassVar = threading.RLock()

    __slots__ = ('_parser', '_make_parser')

    def __init__(self, make_parser: t.Callable[[], Parser[_T]]):
        super().__init__()
        self._parser: t.Optional[Parser[_T]] = None
        # We set this to `None` to aid the garbage collector.
        self._make_parser: t.Optional[t.Callable[[], Parser[_T]]] = make_parser

    @property
    def parser(self) -> Parser[_T]:
        """The parser that this lazy uses."""
        parser = self._parser
        if parser is None:
            with self._LOCK:
                parser = self._parser
                if parser is None:
                    assert self._make_parser is not None
                    self._parser = parser = self._make_parser()
                    self._make_parser = None
        return parser

    def describe(self) -> str:
        return self.parser.describe()

    def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
        return self.parser.to_open_api(schema)

    def try_parse(self, value: object) -> _T:
        return self.parser.try_parse(value)
