"""This module contains the logic to convert python types into parsers."""

from __future__ import annotations

import collections
import dataclasses
import datetime
import decimal
import enum
import fractions
import types
import typing as t
import uuid
from types import NoneType

from cg_dt_utils import DatetimeWithTimezone

from ._any_value import AnyValue
from ._base import Parser, SimpleValue
from ._enum import EnumValue, SingleEnumValue, StringEnum, StringLiteralAsEnum
from ._lazy import Lazy
from ._list import List, TwoTuple
from ._literal import LiteralBoolean
from ._mapping import (
    BaseFixedMapping,
    DiscriminatedUnion,
    LookupMapping,
    OptionalArgument,
    RequiredArgument,
)
from ._nullable import Nullable
from ._query import QueryParam
from ._rich_value import RichValue
from ._set import Set
from ._utils import Annotated, Literal, is_typeddict


class _SkipConverter(Exception):
    __slots__ = ()


_ConvertPriority = t.NewType('_ConvertPriority', int)


@dataclasses.dataclass(frozen=True, eq=True, order=True)
class ConvertPriority:
    """The priority of a convert, the higher the earlier it will be called."""

    __slots__ = ('_prio',)
    _prio: _ConvertPriority

    @classmethod
    def high(cls) -> 'ConvertPriority':
        """Default high priority."""
        return cls(_ConvertPriority(1000))

    @classmethod
    def default(cls) -> 'ConvertPriority':
        """Default priority."""
        return cls(_ConvertPriority(0))

    def increase(self) -> 'ConvertPriority':
        """Increase the priority."""
        return ConvertPriority(_ConvertPriority(self._prio + 1))

    def decrease(self) -> 'ConvertPriority':
        """Decrease the priority."""
        return ConvertPriority(_ConvertPriority(self._prio - 1))


@dataclasses.dataclass(frozen=True, slots=True)
class _RecursiveManager:
    _doing: set[type] = dataclasses.field(default_factory=set)
    _should_add: set[type] = dataclasses.field(default_factory=set)
    _parsers: dict[type, Parser[t.Any]] = dataclasses.field(
        default_factory=dict
    )

    def recurse(self, ctx: ConvertCtx, typ: type) -> Parser:
        """Convert the given ``typ`` with the given ``ctx`` while handling
        recursive parsers.
        """
        if typ in self._doing:
            self._should_add.add(typ)
            return Lazy(lambda: self._parsers[typ])
        else:
            self._doing.add(typ)
            try:
                res = ctx.update_type(typ).convert()
            finally:
                self._doing.remove(typ)

            if typ in self._should_add:
                self._parsers[typ] = res
                self._should_add.remove(typ)

            return res


@dataclasses.dataclass(frozen=True, slots=True)
class _ParserKeyCache:
    #: The type we are converting.
    typ: type
    #: Are converting for a query.
    from_query: bool
    #: Was a readable parser requested?
    readable: bool


_PARSER_CACHE: dict[_ParserKeyCache, Parser] = {}


@dataclasses.dataclass(frozen=True, slots=True)
class ConvertCtx:
    """A context object for the type we are currently converting."""

    #: The type we are converting.
    typ: type
    #: Are converting for a query.
    from_query: bool = dataclasses.field(default=False)
    #: Was a readable parser requested?
    readable: bool = dataclasses.field(default=False)

    _prev_typs: tuple[type, ...] = dataclasses.field(default_factory=tuple)
    _recurse_manager: _RecursiveManager = dataclasses.field(
        default_factory=_RecursiveManager
    )

    @property
    def origin(self) -> t.Any | None:
        """The ``__origin__`` attribute of ``typ`` if present."""
        return t.get_origin(self.typ)

    def update_type(self, new_typ: t.Type) -> ConvertCtx:
        """Change the type of the context.

        :param new_type: The new type of the context.
        """
        return ConvertCtx(
            typ=new_typ,
            from_query=self.from_query,
            readable=self.readable,
            _prev_typs=(*self._prev_typs, self.typ),
            _recurse_manager=self._recurse_manager,
        )

    def assert_not_query(self, cond: bool = False) -> None:
        """Assert we are not in a query."""
        if self.from_query and not cond:  # pragma: no cover
            self.assert_false(
                '{} is not supported as query param'.format(self.typ)
            )

    def skip(self) -> t.NoReturn:
        """Use a different converter for this type."""
        raise _SkipConverter

    def recurse_with_guard(self, new_typ: t.Type) -> Parser:
        """Convert the given ``new_typ`` with guards in-place to deal with
        recursion.
        """
        return self._recurse_manager.recurse(self, new_typ)

    def convert(self) -> Parser:
        """Convert this context into a parser."""
        key = _ParserKeyCache(self.typ, self.from_query, self.readable)
        cached = _PARSER_CACHE.get(key, None)
        if cached is not None:
            return cached

        for _, check, convert in _CONVERTERS:
            if check(self):
                try:
                    parser = convert(self)
                except _SkipConverter:
                    continue
                else:
                    return _PARSER_CACHE.setdefault(key, parser)
        self.assert_false('No converter for this type')

    def assert_false(self, msg: str) -> t.NoReturn:
        """Raise an ``AssertionError`` with some extra context."""
        prev_path = '.'.join(map(str, self._prev_typs))
        raise AssertionError(
            f'Error when converting {self.typ} {type(self.typ)}: {msg} (origin: {self.origin})'
            f' (path: {prev_path})'
        )


Checker = t.Callable[[ConvertCtx], bool]
Converter = t.Callable[[ConvertCtx], Parser]
_CONVERTERS: t.List[t.Tuple[ConvertPriority, Checker, Converter]] = []


def as_converter(
    checker: Checker,
    priority: ConvertPriority = ConvertPriority.default(),
) -> t.Callable[[Converter], Converter]:
    """Register a function as a convert to create a parser for a type.

    :param checker: A function that checks if this converter should be used for
        the type.
    :param priority: The priority of the checker. The higher it is the earlier
        the registered function will be called.
    """

    def _wrapper(converter: Converter) -> Converter:
        _PARSER_CACHE.clear()
        _CONVERTERS.append((priority, checker, converter))
        _CONVERTERS.sort(key=lambda el: el[0], reverse=True)
        return converter

    return _wrapper


def remove_converter(converter: Converter) -> None:
    """Unregister the given converter.

    :param converter: The convert to unregister.
    """
    _PARSER_CACHE.clear()
    global _CONVERTERS
    _CONVERTERS = [c for c in _CONVERTERS if c[-1] != converter]


def get_required_keys(typ: t.Type) -> t.Set[str]:
    """Retrieve the required keys from a given type hinted object.

    This function specifically targets Python's `TypedDict` type, which allows
    for optional keys. It uses the `get_type_hints` function from the `typing`
    module to extract the type hints from the given object. It then iterates
    over the annotations, checking for keys with a `NotRequired`
    origin. These keys are considered optional and are discarded from the set
    of required keys.

    :param typ: The type hinted object from which to retrieve the required keys
    :return: A set of strings representing the required keys.
    """
    annotations = t.get_type_hints(typ, include_extras=True)
    required_keys = set(typ.__required_keys__)
    for key, subtyp in annotations.items():
        origin = t.get_origin(subtyp)
        # The reason for these checks:
        # https://docs.python.org/3/library/typing.html#typing.TypedDict.__optional_keys__
        if origin == t.NotRequired:
            required_keys.discard(key)
    return required_keys


def _get_args_typeddict(
    ctx: ConvertCtx,
    get_doc: t.Callable[[str], str] = lambda _: '',
) -> t.Sequence[t.Union[RequiredArgument, OptionalArgument]]:
    args: t.List[t.Union[RequiredArgument, OptionalArgument]] = []
    annotations = t.get_type_hints(ctx.typ, include_extras=True)
    required_keys = get_required_keys(ctx.typ)

    for key, subtyp in annotations.items():
        doc = get_doc(key)

        sub_parse = ctx.recurse_with_guard(subtyp)

        if key in required_keys:
            args.append(
                RequiredArgument(key, sub_parse, doc)  # type: ignore[misc]
            )
        else:
            args.append(
                OptionalArgument(key, sub_parse, doc)  # type: ignore[misc]
            )
    return args


@as_converter(lambda x: is_typeddict(x.typ))
def _convert_typeddict(ctx: ConvertCtx) -> Parser:
    ctx.assert_not_query()
    args = _get_args_typeddict(ctx)
    mapping = BaseFixedMapping(*args, schema=ctx.typ)  # type: ignore[misc]
    return mapping.use_readable_describe(ctx.readable)


@as_converter(lambda x: x.origin in (t.Required, t.NotRequired))
def _convert_required_not_required(ctx: ConvertCtx) -> Parser:
    return ctx.recurse_with_guard(t.get_args(ctx.typ)[0])


@as_converter(
    lambda x: x.typ in (str, int, bool, float), priority=ConvertPriority.high()
)
def _convert_simple(ctx: ConvertCtx) -> Parser:
    if ctx.from_query:
        return getattr(QueryParam, ctx.typ.__name__)
    else:
        return getattr(SimpleValue, ctx.typ.__name__)


@as_converter(lambda x: x.origin in (list, collections.abc.Sequence))
def _convert_list(ctx: ConvertCtx) -> Parser:
    ctx.assert_not_query()
    return List(
        ctx.update_type(t.get_args(ctx.typ)[0]).convert(),
    ).use_readable_describe(ctx.readable)


@as_converter(
    lambda x: x.origin == t.Union or isinstance(x.typ, types.UnionType)
)
def _convert_union(ctx: ConvertCtx) -> Parser:
    typ = ctx.typ
    has_none = NoneType in t.get_args(typ)

    non_nullable = [a for a in t.get_args(typ) if a != NoneType]
    parsers = [
        ctx.update_type(sub_type).convert() for sub_type in non_nullable
    ]
    discriminated = DiscriminatedUnion.maybe_create(parsers)
    res: Parser
    if discriminated.is_just:
        res = discriminated.value
    else:
        res, *rest = parsers
        for item in rest:
            res = res | item
    if not ctx.from_query and has_none:
        return Nullable(res)
    else:
        return res


@as_converter(
    lambda x: x.typ == decimal.Decimal, priority=ConvertPriority.high()
)
def _convert_decimal(_: ConvertCtx) -> Parser:
    return RichValue.Decimal


@as_converter(
    lambda x: x.typ == fractions.Fraction, priority=ConvertPriority.high()
)
def _convert_fraction(_: ConvertCtx) -> Parser:
    return RichValue.Fraction


@as_converter(
    lambda x: (
        x.origin == Literal
        and len(t.get_args(x.typ)) == 1
        and isinstance(t.get_args(x.typ)[0], bool)
    ),
    priority=ConvertPriority.high(),
)
def _convert_bool_literal(ctx: ConvertCtx) -> Parser:
    return LiteralBoolean(t.get_args(ctx.typ)[0])  # type: ignore[misc]


def _is_string_literal(typ: type) -> bool:
    return t.get_origin(typ) == Literal and all(
        isinstance(arg, str) for arg in t.get_args(typ)
    )


@as_converter(
    lambda x: (
        x.origin == Annotated
        and _is_string_literal(t.get_args(x.typ)[0])
        and any(
            isinstance(arg, StringLiteralAsEnum)
            for arg in t.get_args(x.typ)[1:]
        )
    ),
    priority=ConvertPriority.high(),
)
def _convert_string_literal_as_enum(ctx: ConvertCtx) -> Parser:
    args = t.get_args(ctx.typ)
    literal = args[0]
    as_enum = None
    for arg in args[1:]:
        if isinstance(arg, StringLiteralAsEnum):
            as_enum = arg
            break
    assert as_enum is not None

    typ_args = t.get_args(literal)
    enum_vals: StringEnum[t.Any] = StringEnum(*typ_args, as_enum=as_enum)  # type: ignore[misc]
    return enum_vals.use_readable_describe(ctx.readable)


@as_converter(
    lambda x: _is_string_literal(x.typ),
    priority=ConvertPriority.high(),
)
def _convert_string_literal(ctx: ConvertCtx) -> Parser:
    typ_args = t.get_args(ctx.typ)
    enum_vals: StringEnum[t.Any] = StringEnum(*typ_args)  # type: ignore[misc]
    return enum_vals.use_readable_describe(ctx.readable)


@as_converter(
    lambda ctx: (
        ctx.origin == Literal
        and all(isinstance(arg, enum.Enum) for arg in t.get_args(ctx.typ))
    ),
    priority=ConvertPriority.high(),
)
def _convert_enum_value_literal(ctx: ConvertCtx) -> Parser:
    typ_args = t.get_args(ctx.typ)
    enum_vals = SingleEnumValue(*typ_args)
    return enum_vals.use_readable_describe(ctx.readable)


@as_converter(
    lambda x: isinstance(x.typ, enum.EnumMeta), priority=ConvertPriority.high()
)
def _convert_enum(ctx: ConvertCtx) -> Parser:
    return EnumValue(ctx.typ).use_readable_describe(ctx.readable)


@as_converter(
    lambda x: x.origin in (dict, collections.abc.Mapping),
    priority=ConvertPriority.high(),
)
def _convert_lookup_mapping(ctx: ConvertCtx) -> Parser:
    ctx.assert_not_query()

    key, value = t.get_args(ctx.typ)
    if key is not str:
        ctx.skip()
    else:
        return LookupMapping(
            ctx.update_type(value).convert()
        ).use_readable_describe(ctx.readable)


@as_converter(lambda x: x.typ == uuid.UUID, priority=ConvertPriority.high())
def _convert_uuid(_: ConvertCtx) -> Parser:
    return RichValue.UUID


@as_converter(
    lambda x: x.typ == datetime.timedelta, priority=ConvertPriority.high()
)
def _convert_timedelta(_: ConvertCtx) -> Parser:
    return RichValue.TimeDelta


@as_converter(
    lambda x: x.typ == DatetimeWithTimezone, priority=ConvertPriority.high()
)
def _convert_datetime(_: ConvertCtx) -> Parser:
    return RichValue.DateTime


@as_converter(
    lambda x: x.typ == datetime.date, priority=ConvertPriority.high()
)
def _convert_date(_: ConvertCtx) -> Parser:
    return RichValue.Date


@as_converter(lambda x: t.cast(object, x.typ) == t.Any)
def _convert_any_value(_: ConvertCtx) -> Parser:
    return AnyValue


@as_converter(
    lambda x: x.origin is tuple and len(t.get_args(x.typ)) == 2,
    priority=ConvertPriority.high(),
)
def _convert_two_tuple(ctx: ConvertCtx) -> Parser:
    ctx.assert_not_query()
    return TwoTuple(
        ctx.update_type(t.get_args(ctx.typ)[0]).convert(),
        ctx.update_type(t.get_args(ctx.typ)[1]).convert(),
    ).use_readable_describe(ctx.readable)


@as_converter(lambda x: x.origin is set)
def _convert_set(ctx: ConvertCtx) -> Parser:
    ctx.assert_not_query()
    return Set(
        ctx.update_type(t.get_args(ctx.typ)[0]).convert(),
    ).use_readable_describe(ctx.readable)


@as_converter(lambda x: x.typ is object)
def _convert_object(ctx: ConvertCtx) -> Parser:
    ctx.assert_not_query()
    return AnyValue


@as_converter(lambda x: isinstance(x.typ, t.TypeAliasType))
def _convert_type_alias(ctx: ConvertCtx) -> Parser:
    return ctx.update_type(getattr(ctx.typ, '__value__')).convert()


@as_converter(lambda x: x.typ is NoneType)
def _convert_none(ctx: ConvertCtx) -> Parser:
    return SimpleValue.none
