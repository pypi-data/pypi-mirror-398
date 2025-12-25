"""The endpoints for snippet objects.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import os
import typing as t

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from .. import paginated, parsers, utils

if t.TYPE_CHECKING or os.getenv("CG_EAGERIMPORT", False):
    from .. import client
    from ..models.create_snippet_data import CreateSnippetData
    from ..models.patch_snippet_data import PatchSnippetData
    from ..models.snippet import Snippet


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class SnippetService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def create(
        self: SnippetService[client.AuthenticatedClient],
        json_body: CreateSnippetData,
    ) -> Snippet:
        """Add or modify a `Snippet` by key.

        :param json_body: The body of the request. See
            :class:`.CreateSnippetData` for information about the possible
            fields. You can provide this data as a :class:`.CreateSnippetData`
            or as a dictionary.

        :returns: A response containing the JSON serialized snippet and return
                  code 201.
        """

        url = "/api/v1/snippet"
        params = None

        with self.__client as client:
            resp = client.http.put(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.snippet import Snippet

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(Snippet)
            ).try_parse(resp)

        from ..models.any_error import AnyError

        raise utils.get_error(
            resp,
            (
                (
                    (400, 409, 401, 403, 404, 429, 500),
                    utils.unpack_union(AnyError),
                ),
            ),
        )

    def delete(
        self: SnippetService[client.AuthenticatedClient],
        *,
        snippet_id: int,
    ) -> None:
        """Delete the `Snippet` with the given id.

        :param snippet_id: The id of the snippet

        :returns: An empty response with return code 204
        """

        url = "/api/v1/snippets/{snippetId}".format(snippetId=snippet_id)
        params = None

        with self.__client as client:
            resp = client.http.delete(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 204):
            return parsers.ConstantlyParser(None).try_parse(resp)

        from ..models.any_error import AnyError

        raise utils.get_error(
            resp,
            (
                (
                    (400, 409, 401, 403, 404, 429, 500),
                    utils.unpack_union(AnyError),
                ),
            ),
        )

    def patch(
        self: SnippetService[client.AuthenticatedClient],
        json_body: PatchSnippetData,
        *,
        snippet_id: int,
    ) -> None:
        """Modify the `Snippet` with the given id.

        :param json_body: The body of the request. See
            :class:`.PatchSnippetData` for information about the possible
            fields. You can provide this data as a :class:`.PatchSnippetData`
            or as a dictionary.
        :param snippet_id: The id of the snippet to change.

        :returns: An empty response with return code 204.
        """

        url = "/api/v1/snippets/{snippetId}".format(snippetId=snippet_id)
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 204):
            return parsers.ConstantlyParser(None).try_parse(resp)

        from ..models.any_error import AnyError

        raise utils.get_error(
            resp,
            (
                (
                    (400, 409, 401, 403, 404, 429, 500),
                    utils.unpack_union(AnyError),
                ),
            ),
        )

    def get_all(
        self: SnippetService[client.AuthenticatedClient],
        *,
        page_size: int = 20,
    ) -> paginated.Response[Snippet]:
        """Get all snippets of the current user.

        :param page_size: The size of a single page, maximum is 50.

        :returns: An array containing all snippets for the currently logged in
                  user.
        """

        url = "/api/v1/snippets/"
        params: t.Dict[str, str | int | bool] = {
            "page-size": page_size,
        }

        if t.TYPE_CHECKING:
            import httpx

        def do_request(next_token: str | None) -> httpx.Response:
            if next_token is None:
                params.pop("next-token", "")
            else:
                params["next-token"] = next_token
            with self.__client as client:
                resp = client.http.get(url=url, params=params)
            utils.log_warnings(resp)

            return resp

        def parse_response(resp: httpx.Response) -> t.Sequence[Snippet]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.snippet import Snippet

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(Snippet))
                ).try_parse(resp)

            from ..models.any_error import AnyError

            raise utils.get_error(
                resp,
                (
                    (
                        (400, 409, 401, 403, 404, 429, 500),
                        utils.unpack_union(AnyError),
                    ),
                ),
            )

        return paginated.Response(do_request, parse_response)
