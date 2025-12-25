"""This module contains parsers for sets."""

import typing as t

from ._base import Parser
from ._list import List
from ._swagger_utils import OpenAPISchema
from ._utils import T_COV as _T_COV

__all__ = ('Set',)


class Set(t.Generic[_T_COV], Parser[set[_T_COV]]):
    """A parser for a list homogeneous values."""

    __slots__ = ('__list_parser',)

    def __init__(self, el_type: Parser[_T_COV]):
        super().__init__()
        self.__list_parser = List(el_type).add_open_api_metadata(
            'x-is-set-type',
            True,
        )

    def describe(self) -> str:
        return self.__list_parser.describe()

    def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
        return self.__list_parser.to_open_api(schema)

    def try_parse(self, value: object) -> set[_T_COV]:
        if isinstance(value, set):
            value = list(value)
        return set(self.__list_parser.try_parse(value))
