"""The endpoints for about objects.

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
    from ..models.about import About


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class AboutService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get(
        self,
        *,
        health: Maybe[str] = Nothing,
        tenant_id: Maybe[str] = Nothing,
    ) -> About:
        """Get information about this CodeGrade instance.

        :param health: Key required to view instance health information.
        :param tenant_id: The id of the tenant to get the site settings for.

        :returns: The about object for this instance.
        """

        url = "/api/v1/about"
        params: t.Dict[str, str | int | bool] = {}
        health_as_maybe = maybe_from_nullable(health)
        if health_as_maybe.is_just:
            params["health"] = health_as_maybe.value
        tenant_id_as_maybe = maybe_from_nullable(tenant_id)
        if tenant_id_as_maybe.is_just:
            params["tenant_id"] = tenant_id_as_maybe.value

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.about import About

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(About)
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
