"""The endpoints for tenant objects.

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
    from ..models.all_site_settings import AllSiteSettings
    from ..models.coupon_data_parser import CouponDataParser
    from ..models.create_tenant_data import CreateTenantData
    from ..models.extended_tenant import ExtendedTenant
    from ..models.lti_provider_base import LTIProviderBase
    from ..models.no_permissions import NoPermissions
    from ..models.patch_role_tenant_data import PatchRoleTenantData
    from ..models.patch_settings_tenant_data import PatchSettingsTenantData
    from ..models.patch_tenant_data import PatchTenantData
    from ..models.put_price_tenant_data import PutPriceTenantData
    from ..models.tenant import Tenant
    from ..models.tenant_coupon import TenantCoupon
    from ..models.tenant_permissions import TenantPermissions
    from ..models.tenant_price import TenantPrice
    from ..models.tenant_role_as_json_with_perms import (
        TenantRoleAsJSONWithPerms,
    )
    from ..models.tenant_statistics import TenantStatistics


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class TenantService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all(
        self,
        *,
        q: str = "",
        page_size: int = 10,
    ) -> paginated.Response[Tenant]:
        """Get all tenants of an instance.

        :param q: Only find tenants with a name matching this search query.
        :param page_size: The size of a single page, maximum is 100.

        :returns: All the tenants of this instance that the user is allowed to
                  see.
        """

        url = "/api/v1/tenants/"
        params: t.Dict[str, str | int | bool] = {
            "q": q,
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

        def parse_response(resp: httpx.Response) -> t.Sequence[Tenant]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.tenant import Tenant

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(Tenant))
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
        self: TenantService[client.AuthenticatedClient],
        multipart_data: CreateTenantData,
    ) -> ExtendedTenant:
        """Create a new tenant.

        :param multipart_data: The data that should form the body of the
            request. See :class:`.CreateTenantData` for information about the
            possible fields.

        :returns: The newly created tenant.
        """

        url = "/api/v1/tenants/"
        params = None

        data, files = utils.to_multipart(utils.to_dict(multipart_data))

        with self.__client as client:
            resp = client.http.post(
                url=url, files=files, data=data, params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_tenant import ExtendedTenant

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedTenant)
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

    def create_tenant_coupon(
        self: TenantService[client.AuthenticatedClient],
        json_body: CouponDataParser,
        *,
        tenant_id: str,
    ) -> TenantCoupon:
        """Create a new coupon valid to redeem any course in a tenant, by
        Tenant id.

        :param json_body: The body of the request. See
            :class:`.CouponDataParser` for information about the possible
            fields. You can provide this data as a :class:`.CouponDataParser`
            or as a dictionary.
        :param tenant_id: The tenant that defines the scopes of the coupons.

        :returns: The coupon created for this tenant.
        """

        url = "/api/v1/tenants/{tenantId}/coupons".format(tenantId=tenant_id)
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.tenant_coupon import TenantCouponParser

            return parsers.JsonResponseParser(TenantCouponParser).try_parse(
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

    def delete_tenant_coupon(
        self: TenantService[client.AuthenticatedClient],
        *,
        tenant_id: str,
        coupon_id: str,
    ) -> None:
        """Delete a coupon.

        :param tenant_id: The id of the tenant price the coupon is connected
            to.
        :param coupon_id: The id of the coupon you want to delete.

        :returns: Nothing
        """

        url = "/api/v1/tenants/{tenantId}/coupons/{couponId}".format(
            tenantId=tenant_id, couponId=coupon_id
        )
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

    def update_tenant_coupon(
        self: TenantService[client.AuthenticatedClient],
        json_body: CouponDataParser,
        *,
        tenant_id: str,
        coupon_id: str,
    ) -> TenantCoupon:
        """Update the given coupon with new values.

        :param json_body: The body of the request. See
            :class:`.CouponDataParser` for information about the possible
            fields. You can provide this data as a :class:`.CouponDataParser`
            or as a dictionary.
        :param tenant_id: The tenant that defines the scopes of the coupons.
        :param coupon_id: The id of the coupon you want to update.

        :returns: The updated coupon
        """

        url = "/api/v1/tenants/{tenantId}/coupons/{couponId}".format(
            tenantId=tenant_id, couponId=coupon_id
        )
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.tenant_coupon import TenantCouponParser

            return parsers.JsonResponseParser(TenantCouponParser).try_parse(
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

    def put_price(
        self: TenantService[client.AuthenticatedClient],
        json_body: PutPriceTenantData,
        *,
        tenant_id: str,
    ) -> TenantPrice:
        """Update the price of the given course.

        :param json_body: The body of the request. See
            :class:`.PutPriceTenantData` for information about the possible
            fields. You can provide this data as a :class:`.PutPriceTenantData`
            or as a dictionary.
        :param tenant_id: The id of the tenant for which you want to update the
            price.

        :returns: The created or updated price.
        """

        url = "/api/v1/tenants/{tenantId}/price".format(tenantId=tenant_id)
        params = None

        with self.__client as client:
            resp = client.http.put(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.tenant_price import TenantPrice

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(TenantPrice)
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

    def delete_price(
        self: TenantService[client.AuthenticatedClient],
        *,
        tenant_id: str,
    ) -> None:
        """Update the price of the given course.

        :param tenant_id: The id of the tenant for which you want to delete the
            price.

        :returns: Nothing.
        """

        url = "/api/v1/tenants/{tenantId}/price".format(tenantId=tenant_id)
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

    def get_all_tenant_coupons(
        self: TenantService[client.AuthenticatedClient],
        *,
        tenant_id: str,
        page_size: int = 20,
    ) -> paginated.Response[TenantCoupon]:
        """Retrieves all visible tenant coupon for the tenant linked to the
        tenant.

        :param tenant_id: The tenant that defines the scopes of the coupons.
        :param page_size: The size of a single page, maximum is 50.

        :returns: The list of available coupons.
        """

        url = "/api/v1/tenants/{tenantId}/coupons/".format(tenantId=tenant_id)
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

        def parse_response(resp: httpx.Response) -> t.Sequence[TenantCoupon]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.tenant_coupon import TenantCouponParser

                return parsers.JsonResponseParser(
                    rqa.List(TenantCouponParser)
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

    def get(
        self,
        *,
        tenant_id: str,
    ) -> ExtendedTenant:
        """Get a tenant by id.

        :param tenant_id: The id of the tenant you want to retrieve.

        :returns: The tenant with the given id.
        """

        url = "/api/v1/tenants/{tenantId}".format(tenantId=tenant_id)
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_tenant import ExtendedTenant

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedTenant)
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
        self: TenantService[client.AuthenticatedClient],
        json_body: PatchTenantData,
        *,
        tenant_id: str,
    ) -> ExtendedTenant:
        """Update a tenant by id.

        :param json_body: The body of the request. See
            :class:`.PatchTenantData` for information about the possible
            fields. You can provide this data as a :class:`.PatchTenantData` or
            as a dictionary.
        :param tenant_id: The id of the tenant you want to update.

        :returns: The updated tenant.
        """

        url = "/api/v1/tenants/{tenantId}".format(tenantId=tenant_id)
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_tenant import ExtendedTenant

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedTenant)
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

    def get_logo(
        self,
        *,
        tenant_id: str,
        dark: bool = False,
    ) -> bytes:
        """Get the logo of a tenant.

        :param tenant_id: The id of the tenant for which you want to get the
            logo.
        :param dark: If truhty the retrieved logo will be suited for the dark
            theme.

        :returns: The logo of the tenant.
        """

        url = "/api/v1/tenants/{tenantId}/logo".format(tenantId=tenant_id)
        params: t.Dict[str, str | int | bool] = {
            "dark": dark,
        }

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            return parsers.ResponsePropertyParser("content", bytes).try_parse(
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

    def get_lti_providers(
        self: TenantService[client.AuthenticatedClient],
        *,
        tenant_id: str,
        page_size: int = 20,
    ) -> paginated.Response[LTIProviderBase]:
        """List all LTI providers for this tenant.

        :param tenant_id: The id of the tenant to get the LTI providers for.
        :param page_size: The size of a single page, maximum is 50.

        :returns: A list of all known LTI providers.
        """

        url = "/api/v1/tenants/{tenantId}/lti_providers/".format(
            tenantId=tenant_id
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

    def get_permissions(
        self: TenantService[client.AuthenticatedClient],
        *,
        tenant_id: str,
    ) -> t.Union[TenantPermissions, NoPermissions]:
        """Get the permissions of the logged in user for this tenant.

        If the user does not have an associated role within the tenant, the
        global permissions of the user are returned.

        :param tenant_id: The tenant for which to get the permissions.

        :returns: The courses for this tenant.
        """

        url = "/api/v1/tenants/{tenantId}/permissions/".format(
            tenantId=tenant_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.no_permissions import NoPermissions
            from ..models.tenant_permissions import TenantPermissions

            return parsers.JsonResponseParser(
                parsers.make_union(
                    parsers.ParserFor.make(TenantPermissions),
                    parsers.ParserFor.make(NoPermissions),
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

    def get_roles(
        self: TenantService[client.AuthenticatedClient],
        *,
        tenant_id: str,
    ) -> t.Sequence[TenantRoleAsJSONWithPerms]:
        """Get all roles of this tenant with their permissions

        :param tenant_id: The tenant to get the roles for.

        :returns: An array of roles.
        """

        url = "/api/v1/tenants/{tenantId}/roles/".format(tenantId=tenant_id)
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.tenant_role_as_json_with_perms import (
                TenantRoleAsJSONWithPerms,
            )

            return parsers.JsonResponseParser(
                rqa.List(parsers.ParserFor.make(TenantRoleAsJSONWithPerms))
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

    def get_settings(
        self,
        *,
        tenant_id: str,
        only_frontend: bool = False,
    ) -> AllSiteSettings:
        """Get the settings for this tenant.

        :param tenant_id: The tenant for which to get the settings.
        :param only_frontend: Get only the frontend settings. When `True` the
            returned mapping will contain all frontend settings, even those
            that only have a global value.

        :returns: The settings for this tenant.
        """

        url = "/api/v1/tenants/{tenantId}/settings/".format(tenantId=tenant_id)
        params: t.Dict[str, str | int | bool] = {
            "only_frontend": only_frontend,
        }

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
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

    def patch_settings(
        self: TenantService[client.AuthenticatedClient],
        json_body: PatchSettingsTenantData,
        *,
        tenant_id: str,
    ) -> AllSiteSettings:
        """Update the settings for this tenant.

        :param json_body: The body of the request. See
            :class:`.PatchSettingsTenantData` for information about the
            possible fields. You can provide this data as a
            :class:`.PatchSettingsTenantData` or as a dictionary.
        :param tenant_id: The tenant to update the settings for.

        :returns: The updated tenant settings.
        """

        url = "/api/v1/tenants/{tenantId}/settings/".format(tenantId=tenant_id)
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

    def get_stats(
        self: TenantService[client.AuthenticatedClient],
        *,
        tenant_id: str,
    ) -> TenantStatistics:
        """Get the statistics of a tenant.

        :param tenant_id: The id of the tenant for which you want to get the
            statistics.

        :returns: The statistics of the specified tenant.
        """

        url = "/api/v1/tenants/{tenantId}/statistics/".format(
            tenantId=tenant_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.tenant_statistics import TenantStatistics

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(TenantStatistics)
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

    def patch_role(
        self: TenantService[client.AuthenticatedClient],
        json_body: PatchRoleTenantData,
        *,
        tenant_id: str,
        role_id: int,
    ) -> None:
        """Update the `Permission` of a given `TenantRole`.

        :param json_body: The body of the request. See
            :class:`.PatchRoleTenantData` for information about the possible
            fields. You can provide this data as a
            :class:`.PatchRoleTenantData` or as a dictionary.
        :param tenant_id: The tenant to patch the role for.
        :param role_id: The id of the tenant role.

        :returns: An empty response with return code 204.
        """

        url = "/api/v1/tenants/{tenantId}/roles/{roleId}".format(
            tenantId=tenant_id, roleId=role_id
        )
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
