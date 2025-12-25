"""The endpoints for transaction objects.

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
    from ..models.course_purchase import CoursePurchase
    from ..models.paddle_payment_redirect import PaddlePaymentRedirect
    from ..models.user_access_pass import UserAccessPass


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class TransactionService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_paddle_redirect(
        self: TransactionService[client.AuthenticatedClient],
        *,
        external_transaction_id: str,
    ) -> PaddlePaymentRedirect:
        """Get the info required to redirect from the paddle to the after pay
        page.

        The redirect URL will be deleted after this request.

        :param external_transaction_id: The Paddle transaction id.

        :returns: The redirect info.
        """

        url = "/api/v1/paddle_transactions/{externalTransactionId}".format(
            externalTransactionId=external_transaction_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.paddle_payment_redirect import PaddlePaymentRedirect

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(PaddlePaymentRedirect)
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
        self: TransactionService[client.AuthenticatedClient],
        *,
        transaction_id: str,
    ) -> t.Union[CoursePurchase, UserAccessPass]:
        """Get a transaction by id.

        :param transaction_id: The id of the transaction you want to get.

        :returns: The found transaction.
        """

        url = "/api/v1/transactions/{transactionId}".format(
            transactionId=transaction_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.course_purchase import CoursePurchase
            from ..models.user_access_pass import UserAccessPass

            return parsers.JsonResponseParser(
                parsers.make_union(
                    parsers.ParserFor.make(CoursePurchase),
                    parsers.ParserFor.make(UserAccessPass),
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

    def refund(
        self: TransactionService[client.AuthenticatedClient],
        *,
        transaction_id: str,
    ) -> t.Union[CoursePurchase, UserAccessPass]:
        """Refund a transaction.

        :param transaction_id: The id of the transaction you want to get.

        :returns: The found transaction.
        """

        url = "/api/v1/transactions/{transactionId}/refund".format(
            transactionId=transaction_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.course_purchase import CoursePurchase
            from ..models.user_access_pass import UserAccessPass

            return parsers.JsonResponseParser(
                parsers.make_union(
                    parsers.ParserFor.make(CoursePurchase),
                    parsers.ParserFor.make(UserAccessPass),
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
