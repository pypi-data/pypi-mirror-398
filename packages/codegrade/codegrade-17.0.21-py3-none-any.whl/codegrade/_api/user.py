"""The endpoints for user objects.

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
    from ..models.access_pass_coupon_usage import AccessPassCouponUsage
    from ..models.course_coupon_usage import CourseCouponUsage
    from ..models.course_purchase import CoursePurchase
    from ..models.extended_user import ExtendedUser
    from ..models.login_user_data import LoginUserData
    from ..models.logout_response import LogoutResponse
    from ..models.logout_user_data import LogoutUserData
    from ..models.patch_user_data import PatchUserData
    from ..models.register_user_data import RegisterUserData
    from ..models.session_restriction_data import SessionRestrictionData
    from ..models.tenant_coupon_usage import TenantCouponUsage
    from ..models.user import User
    from ..models.user_access_pass import UserAccessPass
    from ..models.user_login_response import UserLoginResponse


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class UserService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def patch(
        self: UserService[client.AuthenticatedClient],
        json_body: PatchUserData,
        *,
        user_id: int,
    ) -> ExtendedUser:
        """Update the attributes of a user.

        :param json_body: The body of the request. See :class:`.PatchUserData`
            for information about the possible fields. You can provide this
            data as a :class:`.PatchUserData` or as a dictionary.
        :param user_id: The id of the user you want to change. Currently this
            can only be your own user id.

        :returns: The updated user.
        """

        url = "/api/v1/users/{userId}".format(userId=user_id)
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_user import ExtendedUser

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedUser)
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

    def get_coupon_usages(
        self: UserService[client.AuthenticatedClient],
        *,
        user_id: int,
        page_size: int = 20,
    ) -> paginated.Response[
        t.Union[TenantCouponUsage, CourseCouponUsage, AccessPassCouponUsage]
    ]:
        """Get all the coupons used for the specified user.

        :param user_id: The user to get the coupons used for.
        :param page_size: The size of a single page, maximum is 50.

        :returns: All coupons used for the given user.
        """

        url = "/api/v1/users/{userId}/coupon_usages/".format(userId=user_id)
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
        ) -> t.Sequence[
            t.Union[
                TenantCouponUsage, CourseCouponUsage, AccessPassCouponUsage
            ]
        ]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.access_pass_coupon_usage import (
                    AccessPassCouponUsage,
                )
                from ..models.course_coupon_usage import CourseCouponUsage
                from ..models.tenant_coupon_usage import TenantCouponUsage

                return parsers.JsonResponseParser(
                    rqa.List(
                        parsers.make_union(
                            parsers.ParserFor.make(TenantCouponUsage),
                            parsers.ParserFor.make(CourseCouponUsage),
                            parsers.ParserFor.make(AccessPassCouponUsage),
                        )
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

        return paginated.Response(do_request, parse_response)

    def get_transactions(
        self: UserService[client.AuthenticatedClient],
        *,
        user_id: int,
        page_size: int = 20,
    ) -> paginated.Response[t.Union[CoursePurchase, UserAccessPass]]:
        """Get all transactions for the specified user.

        :param user_id: The user to get the transactions for.
        :param page_size: The size of a single page, maximum is 50.

        :returns: All transactions for the given user.
        """

        url = "/api/v1/users/{userId}/transactions/".format(userId=user_id)
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
        ) -> t.Sequence[t.Union[CoursePurchase, UserAccessPass]]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.course_purchase import CoursePurchase
                from ..models.user_access_pass import UserAccessPass

                return parsers.JsonResponseParser(
                    rqa.List(
                        parsers.make_union(
                            parsers.ParserFor.make(CoursePurchase),
                            parsers.ParserFor.make(UserAccessPass),
                        )
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

        return paginated.Response(do_request, parse_response)

    def get(
        self: UserService[client.AuthenticatedClient],
    ) -> ExtendedUser:
        """Get the info of the currently logged in user.

        :returns: A response containing the JSON serialized user
        """

        url = "/api/v1/login"
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_user import ExtendedUser

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedUser)
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

    def login(
        self,
        json_body: LoginUserData,
    ) -> UserLoginResponse:
        """Login using your username and password.

        :param json_body: The body of the request. See :class:`.LoginUserData`
            for information about the possible fields. You can provide this
            data as a :class:`.LoginUserData` or as a dictionary.

        :returns: A response containing the JSON serialized user
        """

        url = "/api/v1/login"
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.user_login_response import UserLoginResponse

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(UserLoginResponse)
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

    def register(
        self,
        json_body: RegisterUserData,
    ) -> UserLoginResponse:
        """Create a new user.

        :param json_body: The body of the request. See
            :class:`.RegisterUserData` for information about the possible
            fields. You can provide this data as a :class:`.RegisterUserData`
            or as a dictionary.

        :returns: The registered user and an `access_token` that can be used to
                  perform requests as this new user.
        """

        url = "/api/v1/user"
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.user_login_response import UserLoginResponse

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(UserLoginResponse)
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

    def restrict(
        self: UserService[client.AuthenticatedClient],
        json_body: SessionRestrictionData,
    ) -> UserLoginResponse:
        """Revoke a given token.

        :param json_body: The body of the request. See
            :class:`.SessionRestrictionData` for information about the possible
            fields. You can provide this data as a
            :class:`.SessionRestrictionData` or as a dictionary.

        :returns: An new token that has the given restrictions added.
        """

        url = "/api/v1/token/restrict"
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.user_login_response import UserLoginResponse

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(UserLoginResponse)
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

    def logout(
        self,
        multipart_data: LogoutUserData,
    ) -> LogoutResponse:
        """Revoke a given token.

        :param multipart_data: The data that should form the body of the
            request. See :class:`.LogoutUserData` for information about the
            possible fields.

        :returns: An empty 200 response.
        """

        url = "/api/v1/token/revoke"
        params = None

        data, files = utils.to_multipart(utils.to_dict(multipart_data))

        with self.__client as client:
            resp = client.http.post(
                url=url, files=files, data=data, params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.logout_response import LogoutResponse

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(LogoutResponse)
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

    def search(
        self: UserService[client.AuthenticatedClient],
        *,
        q: str,
        exclude_course: Maybe[int] = Nothing,
        page_size: int = 20,
    ) -> paginated.Response[User]:
        """Search for a user by name and username.

        :param q: The string to search for, all SQL wildcard are escaped and
                  spaces are replaced by wildcards.
        :param exclude_course: Exclude all users that are in the given course
            from the search results. You need the permission
            `can_list_course_users` on this course to use this parameter.
        :param page_size: The size of a single page, maximum is 50.

        :returns: The users that match the given query string.
        """

        url = "/api/v1/users/"
        params: t.Dict[str, str | int | bool] = {
            "q": q,
            "page-size": page_size,
        }
        exclude_course_as_maybe = maybe_from_nullable(exclude_course)
        if exclude_course_as_maybe.is_just:
            params["exclude_course"] = exclude_course_as_maybe.value

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

        def parse_response(resp: httpx.Response) -> t.Sequence[User]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.user import UserParser

                return parsers.JsonResponseParser(
                    rqa.List(UserParser)
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
