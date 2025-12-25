"""The utils to use pagination in CodeGrade.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import collections.abc
import typing as t

import httpx

_T = t.TypeVar("_T")


class Response(t.Generic[_T], collections.abc.Iterable[_T]):
    """A paginated response."""

    __slots__ = (
        "__do_request",
        "__make_data",
        "__token",
        "__page",
    )

    def __init__(
        self,
        do_request: t.Callable[[str | None], httpx.Response],
        make_data: t.Callable[[httpx.Response], t.Sequence[_T]],
    ) -> None:
        self.__do_request = do_request
        self.__make_data = make_data
        self.__token: None | str = None
        self.__page: t.Sequence[_T] | None = self.__get_page_no_check()

    def __get_page_no_check(self) -> t.Sequence[_T]:
        response = self.__do_request(self.__token)
        result = self.__make_data(response)
        self.__token = response.headers.get("Next-Token")
        return result

    @property
    def finished(self) -> bool:
        return self.__page is None and self.__token is None

    def get_next_page(self) -> t.Sequence[_T]:
        """Get the next page.

        This method is useful if you want to have control over exactly how many
        pages you want to request.
        """
        page = self.__page
        if page is None:
            if self.__token is None:
                raise StopIteration
            return self.__get_page_no_check()
        else:
            self.__page = None
            return page

    def __iter__(self) -> t.Iterator[_T]:
        """Iterate over all items in the collection."""
        while True:
            try:
                yield from self.get_next_page()
            except StopIteration:
                return
