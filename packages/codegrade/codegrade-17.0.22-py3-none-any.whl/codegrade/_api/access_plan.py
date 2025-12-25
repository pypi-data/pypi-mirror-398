"""The endpoints for access_plan objects.

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
    from ..models.access_pass_coupon import AccessPassCoupon
    from ..models.access_pass_coupon_usage import AccessPassCouponUsage
    from ..models.coupon_data_parser import CouponDataParser
    from ..models.create_access_plan_data import CreateAccessPlanData
    from ..models.pay_with_coupon_access_plan_data import (
        PayWithCouponAccessPlanData,
    )
    from ..models.start_payment_access_plan_data import (
        StartPaymentAccessPlanData,
    )
    from ..models.started_transaction import StartedTransaction
    from ..models.tenant_access_plan import TenantAccessPlan
    from ..models.update_access_plan_data import UpdateAccessPlanData


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class AccessPlanService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all(
        self: AccessPlanService[client.AuthenticatedClient],
        *,
        tenant_id: str,
        page_size: int = 20,
    ) -> paginated.Response[TenantAccessPlan]:
        """Get all access plans for a tenant.

        :param tenant_id: The ID of the tenant to get the access plans for.
        :param page_size: The size of a single page, maximum is 50.

        :returns: A paginated list of access plans for the tenant.
        """

        url = "/api/v1/access_plans/"
        params: t.Dict[str, str | int | bool] = {
            "tenant_id": tenant_id,
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
        ) -> t.Sequence[TenantAccessPlan]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.tenant_access_plan import TenantAccessPlan

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(TenantAccessPlan))
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
        self: AccessPlanService[client.AuthenticatedClient],
        json_body: CreateAccessPlanData,
    ) -> TenantAccessPlan:
        """Create a new tenant-wide access plan.

        :param json_body: The body of the request. See
            :class:`.CreateAccessPlanData` for information about the possible
            fields. You can provide this data as a
            :class:`.CreateAccessPlanData` or as a dictionary.

        :returns: The newly created access plan.
        """

        url = "/api/v1/access_plans/"
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.tenant_access_plan import TenantAccessPlan

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(TenantAccessPlan)
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

    def get_coupons(
        self: AccessPlanService[client.AuthenticatedClient],
        *,
        plan_id: str,
        page_size: int = 20,
    ) -> paginated.Response[AccessPassCoupon]:
        """Get all coupons for a tenant access plan.

        :param plan_id: The ID of the access plan.
        :param page_size: The size of a single page, maximum is 50.

        :returns: A paginated list of coupons.
        """

        url = "/api/v1/access_plans/{planId}/coupons/".format(planId=plan_id)
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
        ) -> t.Sequence[AccessPassCoupon]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.access_pass_coupon import AccessPassCouponParser

                return parsers.JsonResponseParser(
                    rqa.List(AccessPassCouponParser)
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

    def create_coupon(
        self: AccessPlanService[client.AuthenticatedClient],
        json_body: CouponDataParser,
        *,
        plan_id: str,
    ) -> AccessPassCoupon:
        """Create a coupon for a tenant access plan.

        :param json_body: The body of the request. See
            :class:`.CouponDataParser` for information about the possible
            fields. You can provide this data as a :class:`.CouponDataParser`
            or as a dictionary.
        :param plan_id: The ID of the access plan.

        :returns: The created coupon.
        """

        url = "/api/v1/access_plans/{planId}/coupons/".format(planId=plan_id)
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.access_pass_coupon import AccessPassCouponParser

            return parsers.JsonResponseParser(
                AccessPassCouponParser
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

    def delete_coupon(
        self: AccessPlanService[client.AuthenticatedClient],
        *,
        plan_id: str,
        coupon_id: str,
    ) -> None:
        """Delete an access pass coupon.

        :param plan_id: The ID of the access plan.
        :param coupon_id: The ID of the coupon to delete.

        :returns: An empty response.
        """

        url = "/api/v1/access_plans/{planId}/coupons/{couponId}".format(
            planId=plan_id, couponId=coupon_id
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

    def update_coupon(
        self: AccessPlanService[client.AuthenticatedClient],
        json_body: CouponDataParser,
        *,
        plan_id: str,
        coupon_id: str,
    ) -> AccessPassCoupon:
        """Update an access pass coupon.

        :param json_body: The body of the request. See
            :class:`.CouponDataParser` for information about the possible
            fields. You can provide this data as a :class:`.CouponDataParser`
            or as a dictionary.
        :param plan_id: The ID of the access plan.
        :param coupon_id: The ID of the coupon to update.

        :returns: The updated coupon.
        """

        url = "/api/v1/access_plans/{planId}/coupons/{couponId}".format(
            planId=plan_id, couponId=coupon_id
        )
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.access_pass_coupon import AccessPassCouponParser

            return parsers.JsonResponseParser(
                AccessPassCouponParser
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

    def start_payment(
        self: AccessPlanService[client.AuthenticatedClient],
        json_body: StartPaymentAccessPlanData,
        *,
        plan_id: str,
        course_id: int,
    ) -> StartedTransaction:
        """Create a new payment for a tenant-wide access plan.

        This transaction will grant the user access to all courses within the
        tenant for the duration specified in the plan.

        :param json_body: The body of the request. See
            :class:`.StartPaymentAccessPlanData` for information about the
            possible fields. You can provide this data as a
            :class:`.StartPaymentAccessPlanData` or as a dictionary.
        :param plan_id: The ID of the access plan to pay for.
        :param course_id: The ID of the course the user was on, to redirect
            back to after successful payment.

        :returns: A transaction object with a `stripe_url` key that can be used
                  to complete the payment.
        """

        url = "/api/v1/access_plans/{planId}/pay".format(planId=plan_id)
        params: t.Dict[str, str | int | bool] = {
            "course_id": course_id,
        }

        with self.__client as client:
            resp = client.http.put(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.started_transaction import StartedTransaction

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(StartedTransaction)
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

    def update(
        self: AccessPlanService[client.AuthenticatedClient],
        json_body: UpdateAccessPlanData,
        *,
        plan_id: str,
    ) -> TenantAccessPlan:
        """Update a tenant access plan.

        :param json_body: The body of the request. See
            :class:`.UpdateAccessPlanData` for information about the possible
            fields. You can provide this data as a
            :class:`.UpdateAccessPlanData` or as a dictionary.
        :param plan_id: The ID of the plan to update.

        :returns: The updated access plan.
        """

        url = "/api/v1/access_plans/{planId}".format(planId=plan_id)
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.tenant_access_plan import TenantAccessPlan

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(TenantAccessPlan)
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

    def pay_with_coupon(
        self: AccessPlanService[client.AuthenticatedClient],
        json_body: PayWithCouponAccessPlanData,
        *,
        plan_id: str,
    ) -> AccessPassCouponUsage:
        """Use a coupon to get access to a tenant-wide plan.

        :param json_body: The body of the request. See
            :class:`.PayWithCouponAccessPlanData` for information about the
            possible fields. You can provide this data as a
            :class:`.PayWithCouponAccessPlanData` or as a dictionary.
        :param plan_id: The ID of the access plan to pay for.

        :returns: The newly created access pass coupon usage record.
        """

        url = "/api/v1/access_plans/{planId}/pay_with_coupon/".format(
            planId=plan_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.access_pass_coupon_usage import AccessPassCouponUsage

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(AccessPassCouponUsage)
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
