"""The endpoints for notification objects.

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
    from ..models.notification import Notification
    from ..models.notification_summary import NotificationSummary
    from ..models.patch_all_notification_data import PatchAllNotificationData
    from ..models.patch_notification_data import PatchNotificationData


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class NotificationService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all(
        self: NotificationService[client.AuthenticatedClient],
        *,
        read: Maybe[bool] = Nothing,
        page_size: int = 20,
    ) -> paginated.Response[Notification]:
        """Get all notifications for the current user.

        :param read: If passed only return notifications that have this read
            status.
        :param page_size: The size of a single page, maximum is 50.

        :returns: A list of notifications.
        """

        url = "/api/v1/notifications/"
        params: t.Dict[str, str | int | bool] = {
            "page-size": page_size,
        }
        read_as_maybe = maybe_from_nullable(read)
        if read_as_maybe.is_just:
            params["read"] = read_as_maybe.value

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

        def parse_response(resp: httpx.Response) -> t.Sequence[Notification]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.notification import NotificationParser

                return parsers.JsonResponseParser(
                    rqa.List(NotificationParser)
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

    def patch_all(
        self: NotificationService[client.AuthenticatedClient],
        json_body: PatchAllNotificationData,
    ) -> t.Sequence[Notification]:
        """Update the read status of multiple notifications.

        :param json_body: The body of the request. See
            :class:`.PatchAllNotificationData` for information about the
            possible fields. You can provide this data as a
            :class:`.PatchAllNotificationData` or as a dictionary.

        :returns: The updated notifications in the same order as given in the
                  body.
        """

        url = "/api/v1/notifications/"
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.notification import NotificationParser

            return parsers.JsonResponseParser(
                rqa.List(NotificationParser)
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

    def get_summary(
        self: NotificationService[client.AuthenticatedClient],
    ) -> NotificationSummary:
        """Get a summary of the user's notifications.

        Provides a capped count of unread notifications for performance.

        :returns: A summary object with unread counts.
        """

        url = "/api/v1/notifications/summary"
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.notification_summary import NotificationSummary

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(NotificationSummary)
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

    def patch(
        self: NotificationService[client.AuthenticatedClient],
        json_body: PatchNotificationData,
        *,
        notification_id: int,
    ) -> Notification:
        """Update the read status for the given notification.

        :param json_body: The body of the request. See
            :class:`.PatchNotificationData` for information about the possible
            fields. You can provide this data as a
            :class:`.PatchNotificationData` or as a dictionary.
        :param notification_id: The id of the notification to update.

        :returns: The updated notification.
        """

        url = "/api/v1/notifications/{notificationId}".format(
            notificationId=notification_id
        )
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.notification import NotificationParser

            return parsers.JsonResponseParser(NotificationParser).try_parse(
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
