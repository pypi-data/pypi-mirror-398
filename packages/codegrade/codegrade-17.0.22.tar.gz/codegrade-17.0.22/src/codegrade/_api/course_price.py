"""The endpoints for course_price objects.

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
    from ..models.coupon_data_parser import CouponDataParser
    from ..models.course_coupon import CourseCoupon
    from ..models.course_coupon_usage import CourseCouponUsage
    from ..models.pay_with_coupon_course_price_data import (
        PayWithCouponCoursePriceData,
    )
    from ..models.start_payment_course_price_data import (
        StartPaymentCoursePriceData,
    )
    from ..models.started_transaction import StartedTransaction
    from ..models.tenant_coupon_usage import TenantCouponUsage


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class CoursePriceService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all_coupons(
        self: CoursePriceService[client.AuthenticatedClient],
        *,
        price_id: str,
        page_size: int = 20,
    ) -> paginated.Response[CourseCoupon]:
        """Get the coupons of a price.

        :param price_id: The price id for which you want to get all coupons.
        :param page_size: The size of a single page, maximum is 50.

        :returns: The coupons (that the current user may see) of the price.
        """

        url = "/api/v1/course_prices/{priceId}/coupons/".format(
            priceId=price_id
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

        def parse_response(resp: httpx.Response) -> t.Sequence[CourseCoupon]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.course_coupon import CourseCouponParser

                return parsers.JsonResponseParser(
                    rqa.List(CourseCouponParser)
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
        self: CoursePriceService[client.AuthenticatedClient],
        json_body: CouponDataParser,
        *,
        price_id: str,
    ) -> CourseCoupon:
        """Create a new coupon for a course price.

        :param json_body: The body of the request. See
            :class:`.CouponDataParser` for information about the possible
            fields. You can provide this data as a :class:`.CouponDataParser`
            or as a dictionary.
        :param price_id: The price you want to create a coupon for.

        :returns: The coupon created for this course price.
        """

        url = "/api/v1/course_prices/{priceId}/coupons/".format(
            priceId=price_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.course_coupon import CourseCouponParser

            return parsers.JsonResponseParser(CourseCouponParser).try_parse(
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

    def delete_coupon(
        self: CoursePriceService[client.AuthenticatedClient],
        *,
        price_id: str,
        coupon_id: str,
    ) -> None:
        """Delete a coupon.

        :param price_id: The id of the price the coupon is connected to.
        :param coupon_id: The id of the coupon you want to delete.

        :returns: Nothing
        """

        url = "/api/v1/course_prices/{priceId}/coupons/{couponId}".format(
            priceId=price_id, couponId=coupon_id
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
        self: CoursePriceService[client.AuthenticatedClient],
        json_body: CouponDataParser,
        *,
        price_id: str,
        coupon_id: str,
    ) -> CourseCoupon:
        """Update the given coupon with new values.

        :param json_body: The body of the request. See
            :class:`.CouponDataParser` for information about the possible
            fields. You can provide this data as a :class:`.CouponDataParser`
            or as a dictionary.
        :param price_id: The price to which the coupon is connected.
        :param coupon_id: The id of the coupon you want to update.

        :returns: The updated coupon
        """

        url = "/api/v1/course_prices/{priceId}/coupons/{couponId}".format(
            priceId=price_id, couponId=coupon_id
        )
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.course_coupon import CourseCouponParser

            return parsers.JsonResponseParser(CourseCouponParser).try_parse(
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

    def start_payment(
        self: CoursePriceService[client.AuthenticatedClient],
        json_body: StartPaymentCoursePriceData,
        *,
        price_id: str,
    ) -> StartedTransaction:
        """Create a new payment for the current user, either for the course
        directly or for a tenant-wide access pass.

        :param json_body: The body of the request. See
            :class:`.StartPaymentCoursePriceData` for information about the
            possible fields. You can provide this data as a
            :class:`.StartPaymentCoursePriceData` or as a dictionary.
        :param price_id: The price of the course you want to gain access to.

        :returns: A transaction object with a `payment_url` key that can be
                  used to complete the payment.
        """

        url = "/api/v1/course_prices/{priceId}/pay".format(priceId=price_id)
        params = None

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

    def pay_with_coupon(
        self: CoursePriceService[client.AuthenticatedClient],
        json_body: PayWithCouponCoursePriceData,
        *,
        price_id: str,
    ) -> t.Union[TenantCouponUsage, CourseCouponUsage]:
        """Pay for a course with a coupon.

        :param json_body: The body of the request. See
            :class:`.PayWithCouponCoursePriceData` for information about the
            possible fields. You can provide this data as a
            :class:`.PayWithCouponCoursePriceData` or as a dictionary.
        :param price_id: The id of the price you want to pay for.

        :returns: Nothing
        """

        url = "/api/v1/course_prices/{priceId}/pay_with_coupon/".format(
            priceId=price_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.course_coupon_usage import CourseCouponUsage
            from ..models.tenant_coupon_usage import TenantCouponUsage

            return parsers.JsonResponseParser(
                parsers.make_union(
                    parsers.ParserFor.make(TenantCouponUsage),
                    parsers.ParserFor.make(CourseCouponUsage),
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
