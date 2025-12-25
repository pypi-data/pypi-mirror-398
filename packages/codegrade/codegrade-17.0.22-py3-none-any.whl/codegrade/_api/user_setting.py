"""The endpoints for user_setting objects.

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
    from ..models.non_present_preference import NonPresentPreference
    from ..models.notification_setting import NotificationSetting
    from ..models.patch_notification_setting_user_setting_data import (
        PatchNotificationSettingUserSettingData,
    )
    from ..models.patch_ui_preference_user_setting_data import (
        PatchUiPreferenceUserSettingData,
    )
    from ..models.present_preference import PresentPreference


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class UserSettingService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all_notification_settings(
        self,
        *,
        token: Maybe[str] = Nothing,
    ) -> NotificationSetting:
        """Update preferences for notifications.

        :param token: The token with which you want to get the preferences, if
            not given the preferences are retrieved for the currently logged in
            user.

        :returns: The preferences for the user as described by the `token`.
        """

        url = "/api/v1/settings/notification_settings/"
        params: t.Dict[str, str | int | bool] = {}
        token_as_maybe = maybe_from_nullable(token)
        if token_as_maybe.is_just:
            params["token"] = token_as_maybe.value

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.notification_setting import NotificationSetting

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(NotificationSetting)
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

    def patch_notification_setting(
        self,
        json_body: PatchNotificationSettingUserSettingData,
        *,
        token: Maybe[str] = Nothing,
    ) -> None:
        """Update preferences for notifications.

        :param json_body: The body of the request. See
            :class:`.PatchNotificationSettingUserSettingData` for information
            about the possible fields. You can provide this data as a
            :class:`.PatchNotificationSettingUserSettingData` or as a
            dictionary.
        :param token: The token with which you want to update the preferences,
            if not given the preferences are updated for the currently logged
            in user.

        :returns: Nothing.
        """

        url = "/api/v1/settings/notification_settings/"
        params: t.Dict[str, str | int | bool] = {}
        token_as_maybe = maybe_from_nullable(token)
        if token_as_maybe.is_just:
            params["token"] = token_as_maybe.value

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

    def get_ui_preference(
        self,
        *,
        name: str,
        token: Maybe[str] = Nothing,
    ) -> t.Union[PresentPreference, NonPresentPreference]:
        """Get ui preferences.

        :param name: The name of the preference you want to get.
        :param token: The token with which you want to get the preferences, if
            not given the preferences are retrieved for the currently logged in
            user.

        :returns: The preferences for the user as described by the `token`.
        """

        url = "/api/v1/settings/ui_preferences/{name}".format(name=name)
        params: t.Dict[str, str | int | bool] = {}
        token_as_maybe = maybe_from_nullable(token)
        if token_as_maybe.is_just:
            params["token"] = token_as_maybe.value

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.non_present_preference import NonPresentPreference
            from ..models.present_preference import PresentPreference

            return parsers.JsonResponseParser(
                parsers.make_union(
                    parsers.ParserFor.make(PresentPreference),
                    parsers.ParserFor.make(NonPresentPreference),
                )
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

    def patch_ui_preference(
        self,
        json_body: PatchUiPreferenceUserSettingData,
        *,
        token: Maybe[str] = Nothing,
    ) -> None:
        """Update ui preferences.

        :param json_body: The body of the request. See
            :class:`.PatchUiPreferenceUserSettingData` for information about
            the possible fields. You can provide this data as a
            :class:`.PatchUiPreferenceUserSettingData` or as a dictionary.
        :param token: The token with which you want to update the preferences,
            if not given the preferences are updated for the currently logged
            in user.

        :returns: Nothing.
        """

        url = "/api/v1/settings/ui_preferences/"
        params: t.Dict[str, str | int | bool] = {}
        token_as_maybe = maybe_from_nullable(token)
        if token_as_maybe.is_just:
            params["token"] = token_as_maybe.value

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
