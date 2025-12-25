"""This module parses enums."""

import dataclasses
import enum
import typing as t

from ._base import Parser, SimpleValue
from ._swagger_utils import OpenAPISchema
from ._utils import T as _T
from ._utils import type_to_name as _type_to_name
from .exceptions import SimpleParseError

_EnumT = t.TypeVar('_EnumT', bound=enum.Enum)

__all__ = ('StringEnum', 'EnumValue', 'StringLiteralAsEnum')


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class StringLiteralAsEnum:
    model_name: str
    description: str


class StringEnum(t.Generic[_T], Parser[_T]):
    """A parser for an list of allowed literal string values."""

    __slots__ = ('opts', 'str_parser', '__as_enum')

    def __init__(
        self,
        *opts: str,
        str_parser: Parser[str] = SimpleValue.str,
        as_enum: StringLiteralAsEnum | None = None,
    ) -> None:
        super().__init__()
        self.opts: t.Final[t.FrozenSet[str]] = frozenset(opts)
        self.str_parser = str_parser
        self.__as_enum = as_enum

    def describe(self) -> str:
        return 'Enum[{}]'.format(', '.join(map(repr, sorted(self.opts))))

    def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
        base = {
            'type': 'string',
            'enum': sorted(self.opts),
        }
        if self.__as_enum is not None:
            return schema.add_as_schema(
                self.__as_enum.model_name,
                {
                    **base,
                    'description': schema.make_comment(
                        self.__as_enum.description
                    ),
                },
                object(),
            )
        return base

    def try_parse(self, value: object) -> _T:
        str_val = self.str_parser.try_parse(value)
        if str_val not in self.opts:
            raise SimpleParseError(self, value)
        return t.cast(_T, str_val)


class EnumValue(t.Generic[_EnumT], Parser[_EnumT]):
    """A parser for an existing enum."""

    __slots__ = ('__typ',)

    def __init__(self, typ: t.Type[_EnumT]) -> None:
        super().__init__()
        self.__typ = typ

    def describe(self) -> str:
        return 'Enum[{}]'.format(
            ', '.join(repr(opt.name) for opt in self.__typ)
        )

    def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
        return schema.add_schema(self.__typ)

    def try_parse(self, value: object) -> _EnumT:
        if not isinstance(value, str):
            raise SimpleParseError(
                self,
                value,
                extra={
                    'message': 'which is of type {}, not string'.format(
                        _type_to_name(type(value))
                    )
                },
            )

        try:
            return self.__typ[value]
        except KeyError as err:
            raise SimpleParseError(self, value) from err


class SingleEnumValue(t.Generic[_EnumT], Parser[_EnumT]):
    __slots__ = ('opts', 'str_parser')

    def __init__(
        self, *values: _EnumT, str_parser: Parser[str] = SimpleValue.str
    ) -> None:
        super().__init__()
        assert values
        self.opts = {val.name: val for val in values}
        self.str_parser = str_parser

    def describe(self) -> str:
        return 'Enum[{}]'.format(', '.join(map(repr, sorted(self.opts))))

    def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
        return {
            'type': 'string',
            'enum': sorted(self.opts),
        }

    def try_parse(self, value: object) -> _EnumT:
        str_val = self.str_parser.try_parse(value)
        try:
            return self.opts[str_val]
        except KeyError as exc:
            raise SimpleParseError(self, value) from exc
