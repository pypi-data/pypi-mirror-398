"""The endpoints for group_set objects.

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
    from ..models.create_group_group_set_data import CreateGroupGroupSetData
    from ..models.extended_group import ExtendedGroup
    from ..models.group import Group
    from ..models.group_set import GroupSet


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class GroupSetService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def copy_group_set(
        self: GroupSetService[client.AuthenticatedClient],
        *,
        group_set_id: int,
    ) -> GroupSet:
        """Copy a GroupSet with all its groups and members.

        This endpoint creates a new group set with the same constraints (min,
        max), groups and members as the original one. Each copied group
        receives a new virtual user and has \"(copy)\" appended to its name.

        :param group_set_id: The id of the group set to copy.

        :returns: The newly created group set.
        """

        url = "/api/v1/group_sets/{groupSetId}/copy".format(
            groupSetId=group_set_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.group_set import GroupSet

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(GroupSet)
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

    def create_group(
        self: GroupSetService[client.AuthenticatedClient],
        json_body: CreateGroupGroupSetData,
        *,
        group_set_id: int,
    ) -> ExtendedGroup:
        """Create a group for the given group set.

        :param json_body: The body of the request. See
            :class:`.CreateGroupGroupSetData` for information about the
            possible fields. You can provide this data as a
            :class:`.CreateGroupGroupSetData` or as a dictionary.
        :param group_set_id: The id of the group set where the new group should
            be placed in.

        :returns: The newly created group.
        """

        url = "/api/v1/group_sets/{groupSetId}/group".format(
            groupSetId=group_set_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_group import ExtendedGroup

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedGroup)
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

    def get(
        self: GroupSetService[client.AuthenticatedClient],
        *,
        group_set_id: int,
    ) -> GroupSet:
        """Get a single `GroupSet` by id.

        :param group_set_id: The id of the group set

        :returns: A response containing the JSON serialized group set.
        """

        url = "/api/v1/group_sets/{groupSetId}".format(groupSetId=group_set_id)
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.group_set import GroupSet

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(GroupSet)
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
        self: GroupSetService[client.AuthenticatedClient],
        *,
        group_set_id: int,
    ) -> None:
        """Delete a `GroupSet`.

        You can only delete a group set if there are no groups in the set and
        no assignment is connected to the group set.

        :param group_set_id: The id of the group set

        :returns: Nothing.
        """

        url = "/api/v1/group_sets/{groupSetId}".format(groupSetId=group_set_id)
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

    def get_all_groups(
        self: GroupSetService[client.AuthenticatedClient],
        *,
        group_set_id: int,
        page_size: int = 20,
    ) -> paginated.Response[Group]:
        """Get all groups for a given group set.

        :param group_set_id: The group set for which the groups should be
            returned.
        :param page_size: The size of a single page, maximum is 50.

        :returns: All the groups for the given group set.
        """

        url = "/api/v1/group_sets/{groupSetId}/groups/".format(
            groupSetId=group_set_id
        )
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

        def parse_response(resp: httpx.Response) -> t.Sequence[Group]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.group import Group

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(Group))
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

    def get_user_group(
        self: GroupSetService[client.AuthenticatedClient],
        *,
        group_set_id: int,
        user_id: int,
    ) -> ExtendedGroup:
        """Get the group for a specific user within a given group set.

        :param group_set_id: The group set to search within.
        :param user_id: The ID of the user whose group is to be found.

        :returns: The single group object for the given user.
        """

        url = "/api/v1/group_sets/{groupSetId}/user/{userId}/group".format(
            groupSetId=group_set_id, userId=user_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_group import ExtendedGroup

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedGroup)
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
