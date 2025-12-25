"""This module contains logic to parse flaks x-www-form-urlencoded requests."""

import typing as t
from typing import Optional

from ._base import Parser as _Parser
from ._swagger_utils import OpenAPISchema as _OpenAPISchema
from ._swagger_utils import Schema as _Schema
from ._swagger_utils import maybe_raise_schema as _maybe_raise_schema
from ._utils import T as _T

try:
    import flask
except ImportError:  # pragma: no cover
    pass

if t.TYPE_CHECKING:  # pragma: no cover
    from ._base import LogReplacer as _LogReplacer


class FormURLEncoded(t.Generic[_T]):
    """This class helps you parse JSON and files from the same request."""

    __slots__ = ('__parser',)

    def __init__(
        self,
        parser: _Parser[_T],
    ) -> None:
        self.__parser = parser

    def __generate_schema(self, open_api: _OpenAPISchema) -> _Schema:
        json_schema = self.__parser.to_open_api(open_api)
        return _Schema(
            typ='multipart/form-data',
            schema=json_schema,
        )

    def from_flask(
        self,
        *,
        log_replacer: Optional['_LogReplacer'] = None,
    ) -> _T:
        """Parse a multipart request from the current flask request.

        :param log_replacer: If passed this function should remove any
            sensitive data from the logs.

        :returns: A tuple, where the first item is the parsed JSON (according
                  to the given parser), and the second argument is a list of
                  the parsed files.
        """
        _maybe_raise_schema(self.__generate_schema)

        body = flask.request.form
        return self.__parser.try_parse_and_log(body, log_replacer=log_replacer)
