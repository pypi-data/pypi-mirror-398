"""The endpoints for site_settings objects.

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
    from ..models.all_site_settings import AllSiteSettings
    from ..models.frontend_site_settings import FrontendSiteSettings
    from ..models.patch_site_settings_data import PatchSiteSettingsData


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class SiteSettingsService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all(
        self,
        *,
        only_frontend: bool = False,
    ) -> t.Union[AllSiteSettings, FrontendSiteSettings]:
        """Get the settings for this CodeGrade instance.

        :param only_frontend: Get only the frontend settings.

        :returns: The site settings for this instance.
        """

        url = "/api/v1/site_settings/"
        params: t.Dict[str, str | int | bool] = {
            "only_frontend": only_frontend,
        }

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.all_site_settings import AllSiteSettings
            from ..models.frontend_site_settings import FrontendSiteSettings

            return parsers.JsonResponseParser(
                parsers.make_union(
                    parsers.ParserFor.make(AllSiteSettings),
                    parsers.ParserFor.make(FrontendSiteSettings),
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

    def patch(
        self: SiteSettingsService[client.AuthenticatedClient],
        json_body: PatchSiteSettingsData,
    ) -> AllSiteSettings:
        """Update the settings for this CodeGrade instance.

        :param json_body: The body of the request. See
            :class:`.PatchSiteSettingsData` for information about the possible
            fields. You can provide this data as a
            :class:`.PatchSiteSettingsData` or as a dictionary.

        :returns: The updated site settings.
        """

        url = "/api/v1/site_settings/"
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.all_site_settings import AllSiteSettings

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(AllSiteSettings)
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
