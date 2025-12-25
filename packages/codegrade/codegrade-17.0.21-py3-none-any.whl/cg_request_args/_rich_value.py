"""
This module contains parsers for values that should be transformed or
restricted in any way.
"""

import datetime
import decimal
import fractions
import re
import typing as t
import uuid

from cg_dt_utils import DatetimeWithTimezone

from ._base import Parser, SimpleParseError, SimpleValue, SimpleValueFactory
from ._mapping import FixedMapping, RequiredArgument
from ._parse_utils import Constraint as _Constraint
from ._parse_utils import Transform as _Transform
from ._swagger_utils import OpenAPISchema
from ._utils import Final, Protocol
from ._utils import T as _T
from .exceptions import ParseError


class _GEComparable(Protocol):
    def __ge__(self: _T, other: _T, /) -> bool: ...


_GEComparableT = t.TypeVar('_GEComparableT', bound=_GEComparable)

__all__ = ('RichValue',)


class _NumberAsString(_Transform[int, str]):
    __slots__ = ()

    def __init__(self, name: str = '_NumberAsString') -> None:
        super().__init__(
            SimpleValue.str,
            self.__to_int,
            name,
        )

    def __to_int(self, value: str) -> int:
        try:
            return int(value)
        except ValueError as exc:
            raise SimpleParseError(self, value) from exc

    def _to_open_api(self, schema: t.Any) -> t.Mapping[str, t.Any]:
        return SimpleValue.int.to_open_api(schema)


class _UUID(_Transform[uuid.UUID, str]):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(SimpleValue.str, self.__transform_to_uuid, 'UUID')

    def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
        return {
            **self._parser.to_open_api(schema),
            'format': 'uuid',
        }

    def __transform_to_uuid(self, value: str) -> uuid.UUID:
        try:
            return uuid.UUID(value)
        except ValueError as exc:
            raise SimpleParseError(
                self,
                value,
                extra={
                    'message': "which can't be parsed as a valid uuid",
                },
            ) from exc


class _Date(_Transform[datetime.date, str]):
    __slots__ = ()

    _ISO8601_DATE_RE = re.compile(
        r'^(?P<year>\d+)-(?P<month>\d\d)-(?P<day>\d\d)$'
    )

    def __init__(self) -> None:
        super().__init__(SimpleValue.str, self.__transform_to_date, 'Date')

    def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
        return {
            **self._parser.to_open_api(schema),
            'format': 'date',
        }

    def __transform_to_date(self, value: str) -> datetime.date:
        match = self._ISO8601_DATE_RE.match(value)
        if match is None:
            raise SimpleParseError(self, value)
        year, month, day = map(int, match.group('year', 'month', 'day'))
        try:
            return datetime.date(year=year, month=month, day=day)
        except ValueError as exc:
            raise SimpleParseError(self, value) from exc


class _DateTime(_Transform[DatetimeWithTimezone, str]):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(
            SimpleValue.str, self.__transform_to_datetime, 'DateTime'
        )

    def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
        return {
            **self._parser.to_open_api(schema),
            'format': 'date-time',
        }

    def __transform_to_datetime(self, value: str) -> DatetimeWithTimezone:
        import dateutil.parser

        try:
            parsed = dateutil.parser.isoparse(value)
        except (ValueError, OverflowError) as exc:
            raise SimpleParseError(
                self,
                value,
                extra={
                    'message': "which can't be parsed as a valid datetime",
                },
            ) from exc
        else:
            return DatetimeWithTimezone.from_datetime(
                parsed, default_tz=datetime.timezone.utc
            )


class _EmailList(_Constraint[str]):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(SimpleValue.str)

    def ok(self, value: str) -> bool:
        import email.utils

        import validate_email

        addresses = email.utils.getaddresses([value.strip()])
        return all(
            validate_email.validate_email(email) for _, email in addresses
        )

    @property
    def name(self) -> str:
        return 'as email list'


class _Password(SimpleValueFactory[str]):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(str)

    def describe(self) -> str:
        return f'password as {super().describe()}'

    def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
        return {
            **super()._to_open_api(schema),
            'format': 'password',
        }

    def try_parse(self, value: object) -> str:
        try:
            return super().try_parse(value)
        except ParseError:
            # Don't raise from as that might leak the value
            raise SimpleParseError(self, found='REDACTED')


class _TimeDeltaFactory(_Transform[datetime.timedelta, t.Union[str, float]]):
    """Factory to create a ISO timedelta parser."""

    __slots__ = ()

    # This updated regex correctly handles all components of the ISO 8601 duration format,
    # including years (Y), months (M), weeks (W), and days (D) in the date part,
    # as well as hours (H), minutes (M), and seconds (S) in the time part (T).
    _ISO8601_DURATION_RE = re.compile(
        r'^(?P<sign>[-+]?)'
        r'P'
        r'(?:(?P<years>\d+(?:\.\d+)?)Y)?'
        r'(?:(?P<months>\d+(?:\.\d+)?)M)?'
        r'(?:(?P<weeks>\d+(?:\.\d+)?)W)?'
        r'(?:(?P<days>\d+(?:\.\d+)?)D)?'
        r'(?:T'
        r'(?:(?P<hours>\d+(?:\.\d+)?)H)?'
        r'(?:(?P<minutes>\d+(?:\.\d+)?)M)?'
        r'(?:(?P<seconds>\d+(?:\.\d+)?)S)?'
        r')?'
        r'$'
    )

    def __init__(self, parser: Parser[t.Union[str, float]]) -> None:
        super().__init__(
            parser,
            self.__to_timedelta,
            'TimeDelta',
        )

    def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
        return {
            **SimpleValue.float.to_open_api(schema),
            'format': 'time-delta',
        }

    def __to_timedelta(self, value: t.Union[str, float]) -> datetime.timedelta:
        if isinstance(value, (int, float)):
            return datetime.timedelta(seconds=value)
        return self.__str_to_timedelta(value)

    def __str_to_timedelta(self, value: str) -> datetime.timedelta:
        match = self._ISO8601_DURATION_RE.match(value)
        if match is None:
            raise SimpleParseError(self, value)

        groupdict: t.Mapping[str, t.Optional[str]] = match.groupdict()
        groups = {k: v for k, v in groupdict.items() if v is not None}
        sign = -1 if groups.get('sign', None) == '-' else 1

        if 'years' in groups or 'months' in groups:
            raise SimpleParseError(
                self,
                value,
                extra={
                    'message': (
                        'Durations with years or months are not supported as '
                        'their length is ambiguous.'
                    )
                },
            )

        return sign * datetime.timedelta(
            days=(
                (float(groups.get('weeks', 0)) * 7)
                + float(groups.get('days', 0))
            ),
            hours=float(groups.get('hours', 0)),
            minutes=float(groups.get('minutes', 0)),
            seconds=float(groups.get('seconds', 0)),
        )


class _NonEmptyString(SimpleValueFactory[str]):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(str)

    def try_parse(self, value: object) -> str:
        nonempty = super().try_parse(value)
        if not nonempty:
            raise SimpleParseError(
                self,
                value,
                extra={
                    'message': 'which is empty',
                },
            )
        return nonempty


class _StringWithoutNullByte(SimpleValueFactory[str]):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(str)

    def try_parse(self, value: object) -> str:
        return super().try_parse(value).replace('\0', '')


class _Fraction(Parser[fractions.Fraction]):
    __slots__ = ()

    _SUB_PARSER = (
        FixedMapping(
            RequiredArgument(
                'n',
                _NumberAsString(),
                'The numerator of the rational.',
            ),
            RequiredArgument(
                'd',
                _NumberAsString(),
                'The denominator of the rational.',
            ),
        )
        .as_schema('Fraction')
        .add_open_api_metadata('x-is-fraction', True)
    )

    def describe(self) -> str:
        return 'Fraction'

    def _to_open_api(self, schema: t.Any) -> t.Mapping[str, t.Any]:
        return self._SUB_PARSER.to_open_api(schema)

    def try_parse(self, value: object) -> fractions.Fraction:
        data = self._SUB_PARSER.try_parse(value)
        return fractions.Fraction(data.n, data.d)


class _FractionAsString(_Transform[fractions.Fraction, str]):
    __slots__ = ()

    _REGEX = r'^[+-]?\d+/[1-9]\d*$'

    def __init__(self, name: str = '_FractionAsString') -> None:
        super().__init__(
            SimpleValue.str,
            self.__to_frac,
            name,
        )

    def __to_frac(self, value: str) -> fractions.Fraction:
        try:
            return fractions.Fraction(value)
        except (ValueError, ZeroDivisionError) as exc:
            raise SimpleParseError(self, value) from exc

    def _to_open_api(self, schema: t.Any) -> t.Mapping[str, t.Any]:
        base = self._parser.to_open_api(schema)
        return {
            **base,
            'pattern': self._REGEX,
            'format': 'fraction',
        }


class _Decimal(_Transform[decimal.Decimal, str]):
    __slots__ = ()

    _REGEX = r'^[+-]?\d+([.]\d+)?$'
    _COMPILED_REGEX = re.compile(_REGEX)

    def __init__(self) -> None:
        super().__init__(
            parser=SimpleValue.str,
            transform=self._transform,
            transform_name='Decimal',
        )

    def _to_open_api(self, schema: t.Any) -> t.Mapping[str, t.Any]:
        base = self._parser.to_open_api(schema)
        return {
            **base,
            'pattern': self._REGEX,
            'format': 'decimal',
        }

    def _transform(self, value: str) -> decimal.Decimal:
        match = self._COMPILED_REGEX.match(value)
        if match is None:
            raise SimpleParseError(self, value)

        return decimal.Decimal(value)


class RichValue:
    """A collection of various constraints and transformers that can be used as
    parsers.
    """

    UUID = _UUID()

    DateTime = _DateTime()

    Date = _Date()

    EmailList = _EmailList()

    Password = _Password()

    TimeDeltaFactory = _TimeDeltaFactory

    TimeDelta = _TimeDeltaFactory(SimpleValue.str | SimpleValue.float)

    NonEmptyString = _NonEmptyString()

    StringWithoutNullByte = _StringWithoutNullByte()

    Decimal = _Decimal()

    Fraction = _Fraction()

    FractionAsString = _FractionAsString()

    class ValueGte(_Constraint[_GEComparableT], t.Generic[_GEComparableT]):
        """Parse a number that is gte than a given minimum."""

        __slots__ = ('__minimum',)

        def __init__(
            self, parser: Parser[_GEComparableT], minimum: _GEComparableT
        ) -> None:
            super().__init__(parser)
            self.__minimum: Final = minimum

        @property
        def name(self) -> str:
            return f'larger than {self.__minimum}'

        def ok(self, value: _GEComparableT) -> bool:
            return value >= self.__minimum

        def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
            return {
                **self._parser.to_open_api(schema),
                'minimum': self.__minimum,
            }
