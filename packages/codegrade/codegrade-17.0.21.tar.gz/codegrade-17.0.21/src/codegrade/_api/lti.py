"""The endpoints for lti objects.

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
    from ..models.create_lti_data import CreateLTIData
    from ..models.deep_link_lti_data import DeepLinkLTIData
    from ..models.launch_second_phase_lti_data import LaunchSecondPhaseLTIData
    from ..models.lti1p1_provider import LTI1p1Provider
    from ..models.lti1p3_provider import LTI1p3Provider
    from ..models.lti_deep_link_response import LTIDeepLinkResponse
    from ..models.lti_launch_result import LTILaunchResult
    from ..models.lti_provider_base import LTIProviderBase
    from ..models.patch1_p1_provider_lti_data import Patch1P1ProviderLTIData
    from ..models.patch1_p3_provider_lti_data import Patch1P3ProviderLTIData
    from ..models.patch_provider_lti_data import PatchProviderLTIData


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class LTIService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all(
        self: LTIService[client.AuthenticatedClient],
        *,
        page_size: int = 20,
    ) -> paginated.Response[LTIProviderBase]:
        """List all known LTI providers for this instance.

        This route is part of the public API.

        :param page_size: The size of a single page, maximum is 50.

        :returns: A list of all known LTI providers.
        """

        url = "/api/v1/lti/providers/"
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
        ) -> t.Sequence[LTIProviderBase]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.lti_provider_base import LTIProviderBaseParser

                return parsers.JsonResponseParser(
                    rqa.List(LTIProviderBaseParser)
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
        self: LTIService[client.AuthenticatedClient],
        json_body: CreateLTIData,
    ) -> LTIProviderBase:
        """Create a new LTI 1.1 or 1.3 provider.

        This route is part of the public API.

        :param json_body: The body of the request. See :class:`.CreateLTIData`
            for information about the possible fields. You can provide this
            data as a :class:`.CreateLTIData` or as a dictionary.

        :returns: The just created provider.
        """

        url = "/api/v1/lti/providers/"
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.lti_provider_base import LTIProviderBaseParser

            return parsers.JsonResponseParser(LTIProviderBaseParser).try_parse(
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

    def deep_link(
        self,
        json_body: DeepLinkLTIData,
        *,
        deep_link_blob_id: str,
    ) -> LTIDeepLinkResponse:
        """Create a deeplink response for the given blob.

        :param json_body: The body of the request. See
            :class:`.DeepLinkLTIData` for information about the possible
            fields. You can provide this data as a :class:`.DeepLinkLTIData` or
            as a dictionary.
        :param deep_link_blob_id: The id of the blob from the first phase, for
            which to create a deeplink.

        :returns: The URL and JWT to use for the deeplink response.
        """

        url = "/api/v1/lti1.3/deep_link/{deepLinkBlobId}".format(
            deepLinkBlobId=deep_link_blob_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.lti_deep_link_response import LTIDeepLinkResponse

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(LTIDeepLinkResponse)
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

    def patch_1p1_provider(
        self,
        json_body: Patch1P1ProviderLTIData,
        *,
        lti_provider_id: str,
        secret: Maybe[str] = Nothing,
    ) -> LTI1p1Provider:
        """Update the given LTI 1.1 provider.

        This route is part of the public api.

        :param json_body: The body of the request. See
            :class:`.Patch1P1ProviderLTIData` for information about the
            possible fields. You can provide this data as a
            :class:`.Patch1P1ProviderLTIData` or as a dictionary.
        :param lti_provider_id: The id of the provider you want to update.
        :param secret: The secret to use to update the provider.

        :returns: The updated provider.
        """

        url = "/api/v1/lti1.1/providers/{ltiProviderId}".format(
            ltiProviderId=lti_provider_id
        )
        params: t.Dict[str, str | int | bool] = {}
        secret_as_maybe = maybe_from_nullable(secret)
        if secret_as_maybe.is_just:
            params["secret"] = secret_as_maybe.value

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.lti1p1_provider import LTI1p1ProviderParser

            return parsers.JsonResponseParser(LTI1p1ProviderParser).try_parse(
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

    def get_1p3_provider(
        self,
        *,
        lti_provider_id: str,
    ) -> LTI1p3Provider:
        """Get a LTI 1.3 provider.

        This route is part of the public API.

        :param lti_provider_id: The id of the provider you want to get.

        :returns: The requested LTI 1.3 provider.
        """

        url = "/api/v1/lti1.3/providers/{ltiProviderId}".format(
            ltiProviderId=lti_provider_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.lti1p3_provider import LTI1p3ProviderParser

            return parsers.JsonResponseParser(LTI1p3ProviderParser).try_parse(
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

    def patch_1p3_provider(
        self,
        json_body: Patch1P3ProviderLTIData,
        *,
        lti_provider_id: str,
        secret: Maybe[str] = Nothing,
    ) -> LTI1p3Provider:
        """Update the given LTI 1.3 provider.

        This route is part of the public API.

        :param json_body: The body of the request. See
            :class:`.Patch1P3ProviderLTIData` for information about the
            possible fields. You can provide this data as a
            :class:`.Patch1P3ProviderLTIData` or as a dictionary.
        :param lti_provider_id: The id of the provider you want to update.
        :param secret: The secret to use to update the provider.

        :returns: The updated LTI 1.3 provider.
        """

        url = "/api/v1/lti1.3/providers/{ltiProviderId}".format(
            ltiProviderId=lti_provider_id
        )
        params: t.Dict[str, str | int | bool] = {}
        secret_as_maybe = maybe_from_nullable(secret)
        if secret_as_maybe.is_just:
            params["secret"] = secret_as_maybe.value

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.lti1p3_provider import LTI1p3ProviderParser

            return parsers.JsonResponseParser(LTI1p3ProviderParser).try_parse(
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

    def get(
        self,
        *,
        lti_provider_id: str,
        secret: Maybe[str] = Nothing,
    ) -> LTIProviderBase:
        """Get a LTI provider.

        This route is part of the public API.

        :param lti_provider_id: The id of the provider you want to get.
        :param secret: The secret to use to update the provider.

        :returns: The requested LTI 1.1 or 1.3 provider.
        """

        url = "/api/v1/lti/providers/{ltiProviderId}".format(
            ltiProviderId=lti_provider_id
        )
        params: t.Dict[str, str | int | bool] = {}
        secret_as_maybe = maybe_from_nullable(secret)
        if secret_as_maybe.is_just:
            params["secret"] = secret_as_maybe.value

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.lti_provider_base import LTIProviderBaseParser

            return parsers.JsonResponseParser(LTIProviderBaseParser).try_parse(
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

    def get_all_1p3(
        self: LTIService[client.AuthenticatedClient],
        *,
        page_size: int = 20,
    ) -> paginated.Response[LTI1p3Provider]:
        """List all known LTI 1.3 providers for this instance.

        This route is part of the public API.

        :param page_size: The size of a single page, maximum is 50.

        :returns: A list of all known LTI 1.3 providers.
        """

        url = "/api/v1/lti1.3/providers/"
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

        def parse_response(resp: httpx.Response) -> t.Sequence[LTI1p3Provider]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.lti1p3_provider import LTI1p3ProviderParser

                return parsers.JsonResponseParser(
                    rqa.List(LTI1p3ProviderParser)
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

    def patch_provider(
        self: LTIService[client.AuthenticatedClient],
        json_body: PatchProviderLTIData,
        *,
        lti_provider_id: str,
    ) -> LTIProviderBase:
        """Update the given LTI provider.

        :param json_body: The body of the request. See
            :class:`.PatchProviderLTIData` for information about the possible
            fields. You can provide this data as a
            :class:`.PatchProviderLTIData` or as a dictionary.
        :param lti_provider_id: The id of the provider you want to update.

        :returns: The updated LTI provider.
        """

        url = "/api/v1/lti/providers/{ltiProviderId}/label".format(
            ltiProviderId=lti_provider_id
        )
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.lti_provider_base import LTIProviderBaseParser

            return parsers.JsonResponseParser(LTIProviderBaseParser).try_parse(
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

    def launch_second_phase(
        self,
        json_body: LaunchSecondPhaseLTIData,
    ) -> LTILaunchResult:
        """Do the second part of an LTI launch. Used internally in our LTI
        Launch page only.

        :param json_body: The body of the request. See
            :class:`.LaunchSecondPhaseLTIData` for information about the
            possible fields. You can provide this data as a
            :class:`.LaunchSecondPhaseLTIData` or as a dictionary.

        :returns: A _LTILaunch instance.
        """

        url = "/api/v1/lti/launch/2"
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.lti_launch_result import LTILaunchResult

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(LTILaunchResult)
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
