"""The endpoints for permission objects.

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
    from ..models.global_perm_map import GlobalPermMap


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class PermissionService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all(
        self: PermissionService[client.AuthenticatedClient],
    ) -> GlobalPermMap:
        """Get all the global permissions or all course permissions for all
        courses for the currently logged in user.

        :returns: A mapping between global permission names and a boolean
                  indicating if the currently logged in user has this
                  permissions is returned.
        """

        url = "/api/v1/permissions/"
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.global_perm_map import GlobalPermMap

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(GlobalPermMap)
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
