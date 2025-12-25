"""The endpoints for role objects.

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
    from ..models.patch_role_data import PatchRoleData
    from ..models.role_as_json_with_perms import RoleAsJSONWithPerms


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class RoleService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all(
        self: RoleService[client.AuthenticatedClient],
        *,
        page_size: int = 20,
    ) -> paginated.Response[RoleAsJSONWithPerms]:
        """Get all global roles with their permissions

        :param page_size: The size of a single page, maximum is 50.

        :returns: An array of all global roles.
        """

        url = "/api/v1/roles/"
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

        def parse_response(
            resp: httpx.Response,
        ) -> t.Sequence[RoleAsJSONWithPerms]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.role_as_json_with_perms import (
                    RoleAsJSONWithPerms,
                )

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(RoleAsJSONWithPerms))
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

    def patch(
        self: RoleService[client.AuthenticatedClient],
        json_body: PatchRoleData,
        *,
        role_id: int,
    ) -> None:
        """Update the `Permission` of a given `Role`.

        :param json_body: The body of the request. See :class:`.PatchRoleData`
            for information about the possible fields. You can provide this
            data as a :class:`.PatchRoleData` or as a dictionary.
        :param role_id: The id of the global role.

        :returns: An empty response with return code 204.
        """

        url = "/api/v1/roles/{roleId}".format(roleId=role_id)
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
