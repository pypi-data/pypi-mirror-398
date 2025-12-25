"""The endpoints for oauth_provider objects.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import os
import typing as t

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from .. import parsers, utils

if t.TYPE_CHECKING or os.getenv("CG_EAGERIMPORT", False):
    from .. import client
    from ..models.oauth_provider import OAuthProvider


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class OAuthProviderService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all(
        self,
    ) -> t.Sequence[OAuthProvider]:
        """Get all OAuth providers connected to this instance.

        :returns: All connected providers.
        """

        url = "/api/v1/oauth_providers/"
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.oauth_provider import OAuthProvider

            return parsers.JsonResponseParser(
                rqa.List(parsers.ParserFor.make(OAuthProvider))
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

    def callback(
        self,
        *,
        provider_id: str,
        state: Maybe[str] = Nothing,
        code: Maybe[str] = Nothing,
        error: Maybe[str] = Nothing,
        error_description: Maybe[str] = Nothing,
    ) -> bytes:
        """The method that is used by OAuth providers after they completed the
        login flow.

        For the precise meaning of the query parameters see RFC 6749.

        :param provider_id: The id of the OAuthProvider that completed the
            flow.
        :param state: The state.
        :param code: The code.
        :param error: The error.
        :param error_description: The description of the error.

        :returns: A response that is not in any defined format.
        """

        url = "/api/v1/oauth_providers/{providerId}/callback".format(
            providerId=provider_id
        )
        params: t.Dict[str, str | int | bool] = {}
        state_as_maybe = maybe_from_nullable(state)
        if state_as_maybe.is_just:
            params["state"] = state_as_maybe.value
        code_as_maybe = maybe_from_nullable(code)
        if code_as_maybe.is_just:
            params["code"] = code_as_maybe.value
        error_as_maybe = maybe_from_nullable(error)
        if error_as_maybe.is_just:
            params["error"] = error_as_maybe.value
        error_description_as_maybe = maybe_from_nullable(error_description)
        if error_description_as_maybe.is_just:
            params["error_description"] = error_description_as_maybe.value

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            return parsers.ResponsePropertyParser("content", bytes).try_parse(
                resp
            )

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
