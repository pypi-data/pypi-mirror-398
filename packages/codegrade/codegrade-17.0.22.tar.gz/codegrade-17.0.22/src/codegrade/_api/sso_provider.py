"""The endpoints for sso_provider objects.

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
    from ..models.create_sso_provider_data import CreateSSOProviderData
    from ..models.saml2_provider import Saml2Provider


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class SSOProviderService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all(
        self,
        *,
        page_size: int = 20,
    ) -> paginated.Response[Saml2Provider]:
        """Get all the SSO providers.

        :param page_size: The size of a single page, maximum is 50.

        :returns: The SSO providers, paginated.
        """

        url = "/api/v1/sso_providers/"
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

        def parse_response(resp: httpx.Response) -> t.Sequence[Saml2Provider]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.saml2_provider import Saml2Provider

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(Saml2Provider))
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

    def create(
        self: SSOProviderService[client.AuthenticatedClient],
        json_body: CreateSSOProviderData,
    ) -> Saml2Provider:
        """Register a new SSO Provider in this instance.

        Users will be able to login using the registered provider.

        The request should contain two files. One named `json` containing the
        json data explained below and one named `logo` containing the backup
        logo.

        :param json_body: The body of the request. See
            :class:`.CreateSSOProviderData` for information about the possible
            fields. You can provide this data as a
            :class:`.CreateSSOProviderData` or as a dictionary.

        :returns: The just created provider.
        """

        url = "/api/v1/sso_providers/"
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.saml2_provider import Saml2Provider

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(Saml2Provider)
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
