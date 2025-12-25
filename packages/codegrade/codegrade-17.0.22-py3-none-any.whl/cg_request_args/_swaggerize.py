"""This module contains code to mark flask routes as public API methods."""

from __future__ import annotations

import dataclasses
import functools
import inspect
import typing as t

from ._mapping import BaseFixedMapping

__all__ = ('swaggerize',)


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class _SwaggerFunc:
    operation_name: str
    no_data: bool
    func: t.Callable
    query_parser: t.Optional['BaseFixedMapping']
    header_parser: t.Optional['BaseFixedMapping']


_SWAGGER_FUNCS: t.Dict[str, t.Dict[t.Optional[str], _SwaggerFunc]] = {}


_NameMapping = t.Mapping[
    t.Literal['GET', 'POST', 'DELETE', 'PATCH', 'PUT'], str
]


def _get_headers(wanted: list[str]) -> dict[str, str]:
    import flask

    headers = flask.request.headers
    result = {}
    for key in wanted:
        try:
            result[key] = headers[key]
        except KeyError:
            pass
    return result


def swaggerize[T, **P](
    operation_name: str | _NameMapping,
    *,
    no_data: bool = False,
) -> t.Callable[[t.Callable[P, T]], t.Callable[P, T]]:
    """Mark this function as a function that should be included in the open api
    docs.

    :param operation_name: The name that the route should have in the client
        API libraries.
    :param no_data: If this is a route that can take input data (``PATCH``,
        ``PUT``, ``POST``), but doesn't you should pass ``True`` here. If you
        don't the function should contain a call to ``from_flask`` as the first
        statement of the function.
    """

    def __wrapper(func: t.Callable[P, T]) -> t.Callable[P, T]:
        if func.__name__ in _SWAGGER_FUNCS:  # pragma: no cover
            raise AssertionError(
                f'The function {func.__name__} was already registered.'
            )

        import flask

        wrapped_func, query_parser = _process_params(
            func,
            'Query',
            lambda _: flask.request.args,
            prefix_to_add='',
        )
        wrapped_func, header_parser = _process_params(
            wrapped_func,
            'Header',
            _get_headers,
            prefix_to_add='cg_',
        )

        func_dict = _SWAGGER_FUNCS.setdefault(func.__name__, {})
        if isinstance(operation_name, str):
            func_dict[None] = _SwaggerFunc(
                operation_name=operation_name,
                no_data=no_data,
                func=func,
                query_parser=query_parser,
                header_parser=header_parser,
            )
        else:
            for method, name in operation_name.items():
                func_dict[method] = _SwaggerFunc(
                    operation_name=name,
                    no_data=no_data,
                    func=func,
                    query_parser=query_parser,
                    header_parser=header_parser,
                )

        return wrapped_func

    return __wrapper


def _process_params[T, **P](
    func: t.Callable[P, T],
    what: str,
    get_params: t.Callable[[list[str]], object],
    prefix_to_add: str,
) -> tuple[t.Callable[P, T], None | BaseFixedMapping[t.Any]]:
    """Process query parameters of the given function.

    All parameters prefixed with ``query_`` are retrieved and parsed from the
    query parameters.
    """
    prefix = f'{what.lower()}_'
    prefix_len = len(prefix)
    parameters = [
        value
        for value in inspect.signature(func, eval_str=True).parameters.values()
        if value.name.startswith(prefix)
    ]
    if not parameters:
        return func, None
    wanted_keys = [
        f'{prefix_to_add}{value.name[prefix_len:]}' for value in parameters
    ]
    query_params = [
        inspect.Parameter(
            name=f'{prefix_to_add}{value.name[prefix_len:]}',
            kind=value.kind,
            default=value.default,
            annotation=value.annotation,
        )
        for value in parameters
    ]

    query_parser = BaseFixedMapping.from_function_parameters_list(
        query_params,
        from_query=True,
    )

    log_msg = f'{what} parameters processed'

    @functools.wraps(func)
    def __inner(*args: P.args, **kwargs: P.kwargs) -> T:
        data = get_params(wanted_keys)
        for key, value in query_parser.try_parse_and_log(
            data,
            msg=log_msg,
        ).items():
            kwargs[f'{prefix}{key[len(prefix_to_add) :]}'] = value
        return func(*args, **kwargs)

    return __inner, query_parser
