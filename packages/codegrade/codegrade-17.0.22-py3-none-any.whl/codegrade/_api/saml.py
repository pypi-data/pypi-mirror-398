"""The endpoints for saml objects.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import os
import typing as t

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing

from .. import parsers, utils

if t.TYPE_CHECKING or os.getenv("CG_EAGERIMPORT", False):
    from .. import client
    from ..models.user_login_response import UserLoginResponse


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class SamlService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_session(
        self,
        *,
        token: str,
    ) -> UserLoginResponse:
        """Get a JWT token for a user after doing a successful launch.

        This method will use various pieces of information from the session
        from the requested user.

        This method can only be used once to retrieve the JWT, as the data will
        be removed after the first request.

        :param token: The token that we will use to verify that you are the
            correct owner of the SAML launch. This data will be cross
            referenced to stored data and your session.

        :returns: A mapping containing one key (`access_token`).
        """

        url = "/api/sso/saml2/jwts/{token}".format(token=token)
        params = None

        with self.__client as client:
            resp = client.http.post(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.user_login_response import UserLoginResponse

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(UserLoginResponse)
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
