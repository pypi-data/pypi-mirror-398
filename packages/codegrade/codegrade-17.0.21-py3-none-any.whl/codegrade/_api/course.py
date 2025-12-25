"""The endpoints for course objects.

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
    from ..models.assignment import Assignment
    from ..models.bulk_enroll_course_data import BulkEnrollCourseData
    from ..models.change_user_role_course_data import ChangeUserRoleCourseData
    from ..models.course import Course
    from ..models.course_authorization import CourseAuthorization
    from ..models.course_bulk_enroll_result import CourseBulkEnrollResult
    from ..models.course_enrollment import CourseEnrollment
    from ..models.course_price import CoursePrice
    from ..models.course_registration_link import CourseRegistrationLink
    from ..models.course_role import CourseRole
    from ..models.course_section import CourseSection
    from ..models.course_snippet import CourseSnippet
    from ..models.course_statistics_as_json import CourseStatisticsAsJSON
    from ..models.create_assignment_course_data import (
        CreateAssignmentCourseData,
    )
    from ..models.create_course_data import CreateCourseData
    from ..models.create_group_set_course_data import CreateGroupSetCourseData
    from ..models.create_role_course_data import CreateRoleCourseData
    from ..models.create_section_course_data import CreateSectionCourseData
    from ..models.create_snippet_course_data import CreateSnippetCourseData
    from ..models.email_users_course_data import EmailUsersCourseData
    from ..models.extended_assignment import ExtendedAssignment
    from ..models.extended_course import ExtendedCourse
    from ..models.extended_course_registration_link import (
        ExtendedCourseRegistrationLink,
    )
    from ..models.extended_course_role import ExtendedCourseRole
    from ..models.group_set import GroupSet
    from ..models.import_into_course_data import ImportIntoCourseData
    from ..models.import_snippets_into_course_data import (
        ImportSnippetsIntoCourseData,
    )
    from ..models.job import Job
    from ..models.patch_course_data import PatchCourseData
    from ..models.patch_role_course_data import PatchRoleCourseData
    from ..models.patch_snippet_course_data import PatchSnippetCourseData
    from ..models.put_enroll_link_course_data import PutEnrollLinkCourseData
    from ..models.put_price_course_data import PutPriceCourseData
    from ..models.register_user_with_link_course_data import (
        RegisterUserWithLinkCourseData,
    )
    from ..models.user_login_response import UserLoginResponse
    from ..models.work import Work


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class CourseService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all(
        self: CourseService[client.AuthenticatedClient],
        *,
        lti_course_id: Maybe[str] = Nothing,
        tenant_id: Maybe[str] = Nothing,
        q: str = "",
        page_size: int = 20,
    ) -> paginated.Response[Course]:
        """Return all Course objects the current user is a member of.

        :param lti_course_id: The id of the course according to the lti
            platform.
        :param tenant_id: The id of the tenant to which you want to limit the
            courses you are searching.
        :param q: Only find courses matching this search query, currently only
                  searches for course names in a fuzzy way.
        :param page_size: The size of a single page, maximum is 50.

        :returns: A response containing the requested courses.
        """

        url = "/api/v1/courses/"
        params: t.Dict[str, str | int | bool] = {
            "q": q,
            "page-size": page_size,
        }
        lti_course_id_as_maybe = maybe_from_nullable(lti_course_id)
        if lti_course_id_as_maybe.is_just:
            params["lti_course_id"] = lti_course_id_as_maybe.value
        tenant_id_as_maybe = maybe_from_nullable(tenant_id)
        if tenant_id_as_maybe.is_just:
            params["tenant_id"] = tenant_id_as_maybe.value

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

        def parse_response(resp: httpx.Response) -> t.Sequence[Course]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.course import Course

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(Course))
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
        self: CourseService[client.AuthenticatedClient],
        json_body: CreateCourseData,
    ) -> ExtendedCourse:
        """Create a new course.

        :param json_body: The body of the request. See
            :class:`.CreateCourseData` for information about the possible
            fields. You can provide this data as a :class:`.CreateCourseData`
            or as a dictionary.

        :returns: A response containing the JSON serialization of the new
                  course
        """

        url = "/api/v1/courses/"
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_course import ExtendedCourse

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedCourse)
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

    def get_course_roles(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        q: str = "",
        page_size: int = 20,
    ) -> paginated.Response[CourseRole]:
        """Get a list of all course roles in a given course.

        :param course_id: The id of the course to get the roles for.
        :param q: Search on the name for the roles.
        :param page_size: The size of a single page, maximum is 50.

        :returns: An array of all course roles for the given course.
        """

        url = "/api/v1/courses/{courseId}/roles/".format(courseId=course_id)
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

        def parse_response(resp: httpx.Response) -> t.Sequence[CourseRole]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.course_role import CourseRole

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(CourseRole))
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

    def create_role(
        self: CourseService[client.AuthenticatedClient],
        json_body: CreateRoleCourseData,
        *,
        course_id: int,
    ) -> ExtendedCourseRole:
        """Add a new `CourseRole` to the given `Course`.

        :param json_body: The body of the request. See
            :class:`.CreateRoleCourseData` for information about the possible
            fields. You can provide this data as a
            :class:`.CreateRoleCourseData` or as a dictionary.
        :param course_id: The id of the course

        :returns: An empty response with return code 204.
        """

        url = "/api/v1/courses/{courseId}/roles/".format(courseId=course_id)
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_course_role import ExtendedCourseRole

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedCourseRole)
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

    def bulk_enroll(
        self: CourseService[client.AuthenticatedClient],
        json_body: BulkEnrollCourseData,
        *,
        course_id: int,
    ) -> CourseBulkEnrollResult:
        """Bulk enroll users into this course.

        All given users are directly enrolled into the course, and they will
        receive an email confirming that they have been enrolled.

        Users that do not exist yet are created, but no password is set yet so
        they cannot log in. Their course enrollment email will include a link
        to a page where they can set their password.

        :param json_body: The body of the request. See
            :class:`.BulkEnrollCourseData` for information about the possible
            fields. You can provide this data as a
            :class:`.BulkEnrollCourseData` or as a dictionary.
        :param course_id: The id of the course in which users should be
            enrolled.

        :returns: A dictionary containing the job sending out the mails, a list
                  of newly created users, and a list of users that could not be
                  created because of SSO incompatibility.
        """

        url = "/api/v1/courses/{courseId}/bulk_enroll/".format(
            courseId=course_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.course_bulk_enroll_result import (
                CourseBulkEnrollResult,
            )

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(CourseBulkEnrollResult)
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

    def create_snippet(
        self: CourseService[client.AuthenticatedClient],
        json_body: CreateSnippetCourseData,
        *,
        course_id: int,
    ) -> CourseSnippet:
        """Add or modify a `CourseSnippet` by key.

        :param json_body: The body of the request. See
            :class:`.CreateSnippetCourseData` for information about the
            possible fields. You can provide this data as a
            :class:`.CreateSnippetCourseData` or as a dictionary.
        :param course_id: The id of the course in which you want to create a
            new snippet.

        :returns: A response containing the JSON serialized snippet and return
                  code 201.
        """

        url = "/api/v1/courses/{courseId}/snippet".format(courseId=course_id)
        params = None

        with self.__client as client:
            resp = client.http.put(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 201):
            from ..models.course_snippet import CourseSnippet

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(CourseSnippet)
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

    def get_group_sets(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        page_size: int = 20,
    ) -> paginated.Response[GroupSet]:
        """Get the all the group sets of a given course.

        :param course_id: The id of the course of which the group sets should
            be retrieved.
        :param page_size: The size of a single page, maximum is 50.

        :returns: A list of group sets.
        """

        url = "/api/v1/courses/{courseId}/group_sets/".format(
            courseId=course_id
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

        def parse_response(resp: httpx.Response) -> t.Sequence[GroupSet]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.group_set import GroupSet

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(GroupSet))
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

    def create_group_set(
        self: CourseService[client.AuthenticatedClient],
        json_body: CreateGroupSetCourseData,
        *,
        course_id: int,
    ) -> GroupSet:
        """Create or update a `GroupSet` in the given course id.

        :param json_body: The body of the request. See
            :class:`.CreateGroupSetCourseData` for information about the
            possible fields. You can provide this data as a
            :class:`.CreateGroupSetCourseData` or as a dictionary.
        :param course_id: The id of the course in which the group set should be
            created or updated. The course id of a group set cannot change.

        :returns: The created or updated group.
        """

        url = "/api/v1/courses/{courseId}/group_sets/".format(
            courseId=course_id
        )
        params = None

        with self.__client as client:
            resp = client.http.put(
                url=url, json=utils.to_dict(json_body), params=params
            )
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

    def get_assignments(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        has_rubric: bool = False,
        has_auto_test: bool = False,
        has_handin_requirements: bool = False,
        division_parent_id: Maybe[int] = Nothing,
        group_set_id: Maybe[int] = Nothing,
        q: str = "",
        page_size: int = 20,
    ) -> paginated.Response[Assignment]:
        """Get all assignments of the given course.

        The returned assignments are sorted by deadline.

        :param course_id: The id of the course
        :param has_rubric: Get only assignments that have a rubric.
        :param has_auto_test: Get only assignments that have a AutoTest
            configuration.
        :param has_handin_requirements: Get only assignments that have hand-in
            requirements.
        :param division_parent_id: Only return assignments matching the given
            division parent id.
        :param group_set_id: Only return assignments that are linked to this
            group set id.
        :param q: Only assignments matching this query will be returned.
        :param page_size: The size of a single page, maximum is 50.

        :returns: A response containing the assignments of the given course
                  sorted by deadline of the assignment
        """

        url = "/api/v1/courses/{courseId}/assignments/".format(
            courseId=course_id
        )
        params: t.Dict[str, str | int | bool] = {
            "has_rubric": has_rubric,
            "has_auto_test": has_auto_test,
            "has_handin_requirements": has_handin_requirements,
            "q": q,
            "page-size": page_size,
        }
        division_parent_id_as_maybe = maybe_from_nullable(division_parent_id)
        if division_parent_id_as_maybe.is_just:
            params["division_parent_id"] = division_parent_id_as_maybe.value
        group_set_id_as_maybe = maybe_from_nullable(group_set_id)
        if group_set_id_as_maybe.is_just:
            params["group_set_id"] = group_set_id_as_maybe.value

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

        def parse_response(resp: httpx.Response) -> t.Sequence[Assignment]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.assignment import Assignment

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(Assignment))
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

    def create_assignment(
        self: CourseService[client.AuthenticatedClient],
        json_body: CreateAssignmentCourseData,
        *,
        course_id: int,
    ) -> ExtendedAssignment:
        """Create a new course for the given assignment.

        :param json_body: The body of the request. See
            :class:`.CreateAssignmentCourseData` for information about the
            possible fields. You can provide this data as a
            :class:`.CreateAssignmentCourseData` or as a dictionary.
        :param course_id: The course to create an assignment in.

        :returns: The newly created assignment.
        """

        url = "/api/v1/courses/{courseId}/assignments/".format(
            courseId=course_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_assignment import ExtendedAssignment

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedAssignment)
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

    def get_all_enroll_links(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        page_size: int = 20,
    ) -> paginated.Response[CourseRegistrationLink]:
        """Get the registration links for the given course.

        :param course_id: The course id for which to get the registration
            links.
        :param page_size: The size of a single page, maximum is 50.

        :returns: An array of registration links.
        """

        url = "/api/v1/courses/{courseId}/registration_links/".format(
            courseId=course_id
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
        ) -> t.Sequence[CourseRegistrationLink]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.course_registration_link import (
                    CourseRegistrationLink,
                )

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(CourseRegistrationLink))
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

    def put_enroll_link(
        self: CourseService[client.AuthenticatedClient],
        json_body: PutEnrollLinkCourseData,
        *,
        course_id: int,
    ) -> CourseRegistrationLink:
        """Create or edit an enroll link.

        :param json_body: The body of the request. See
            :class:`.PutEnrollLinkCourseData` for information about the
            possible fields. You can provide this data as a
            :class:`.PutEnrollLinkCourseData` or as a dictionary.
        :param course_id: The id of the course in which this link should enroll
            users.

        :returns: The created or edited link.
        """

        url = "/api/v1/courses/{courseId}/registration_links/".format(
            courseId=course_id
        )
        params = None

        with self.__client as client:
            resp = client.http.put(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.course_registration_link import (
                CourseRegistrationLink,
            )

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(CourseRegistrationLink)
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

    def get_sections(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        q: str = "",
        page_size: int = 20,
    ) -> paginated.Response[CourseSection]:
        """Get all sections of this course.

        :param course_id: The id of the course to get the sections for.
        :param q: Only find courses sections with a name matching this search
                  query.
        :param page_size: The size of a single page, maximum is 50.

        :returns: A list of all sections connected to this course.
        """

        url = "/api/v1/courses/{courseId}/sections/".format(courseId=course_id)
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

        def parse_response(resp: httpx.Response) -> t.Sequence[CourseSection]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.course_section import CourseSection

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(CourseSection))
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

    def create_section(
        self: CourseService[client.AuthenticatedClient],
        json_body: CreateSectionCourseData,
        *,
        course_id: int,
    ) -> CourseSection:
        """Create a new course section.

        :param json_body: The body of the request. See
            :class:`.CreateSectionCourseData` for information about the
            possible fields. You can provide this data as a
            :class:`.CreateSectionCourseData` or as a dictionary.
        :param course_id: The id of the course to create a section for.

        :returns: The new section.
        """

        url = "/api/v1/courses/{courseId}/sections/".format(courseId=course_id)
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.course_section import CourseSection

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(CourseSection)
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

    def put_price(
        self: CourseService[client.AuthenticatedClient],
        json_body: PutPriceCourseData,
        *,
        course_id: int,
    ) -> CoursePrice:
        """Update the price of the given course.

        :param json_body: The body of the request. See
            :class:`.PutPriceCourseData` for information about the possible
            fields. You can provide this data as a :class:`.PutPriceCourseData`
            or as a dictionary.
        :param course_id: The id of the course for which you want to update the
            price.

        :returns: The created or updated price.
        """

        url = "/api/v1/courses/{courseId}/price".format(courseId=course_id)
        params = None

        with self.__client as client:
            resp = client.http.put(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.course_price import CoursePrice

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(CoursePrice)
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
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
    ) -> None:
        """Update the price of the given course.

        :param course_id: The id of the course for which you want to update the
            price.

        :returns: The created or updated price.
        """

        url = "/api/v1/courses/{courseId}/price".format(courseId=course_id)
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

    def delete_snippet(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        snippet_id: int,
    ) -> None:
        """Delete the `CourseSnippet` with the given id.

        :param course_id: The id of the course in which the snippet is located.
        :param snippet_id: The id of the snippet

        :returns: An empty response with return code 204
        """

        url = "/api/v1/courses/{courseId}/snippets/{snippetId}".format(
            courseId=course_id, snippetId=snippet_id
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

    def patch_snippet(
        self: CourseService[client.AuthenticatedClient],
        json_body: PatchSnippetCourseData,
        *,
        course_id: int,
        snippet_id: int,
    ) -> None:
        """Modify the `CourseSnippet` with the given id.

        :param json_body: The body of the request. See
            :class:`.PatchSnippetCourseData` for information about the possible
            fields. You can provide this data as a
            :class:`.PatchSnippetCourseData` or as a dictionary.
        :param course_id: The id of the course in which the course snippet is
            saved.
        :param snippet_id: The id of the snippet to change.

        :returns: An empty response with return code 204.
        """

        url = "/api/v1/courses/{courseId}/snippets/{snippetId}".format(
            courseId=course_id, snippetId=snippet_id
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

    def get_registration_link(
        self,
        *,
        course_id: int,
        link_id: str,
    ) -> ExtendedCourseRegistrationLink:
        """Get a registration link.

        This route can be used without logging in, i.e. you don't have to be
        enrolled in the course to use this route. This route will not work for
        expired registration links.

        :param course_id: The id of the course to which the registration link
            is connected.
        :param link_id: The id of the registration link.

        :returns: The specified registration link.
        """

        url = "/api/v1/courses/{courseId}/registration_links/{linkId}".format(
            courseId=course_id, linkId=link_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_course_registration_link import (
                ExtendedCourseRegistrationLink,
            )

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedCourseRegistrationLink)
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

    def delete_enroll_link(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        link_id: str,
    ) -> None:
        """Delete the given registration link.

        :param course_id: The id of the course to which the registration link
            is connected.
        :param link_id: The id of the registration link.

        :returns: Nothing.
        """

        url = "/api/v1/courses/{courseId}/registration_links/{linkId}".format(
            courseId=course_id, linkId=link_id
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

    def get_course_role(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        role_id: int,
    ) -> ExtendedCourseRole:
        """Get a list of all course roles in a given course.

        :param course_id: The id of the course to get the roles for.
        :param role_id: The id of the role to get.

        :returns: The requested role.
        """

        url = "/api/v1/courses/{courseId}/roles/{roleId}".format(
            courseId=course_id, roleId=role_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_course_role import ExtendedCourseRole

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedCourseRole)
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

    def delete_role(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        role_id: int,
    ) -> None:
        """Remove a `CourseRole` from the given `Course`.

        :param course_id: The id of the course
        :param role_id: The id of the role you want to delete

        :returns: An empty response with return code 204
        """

        url = "/api/v1/courses/{courseId}/roles/{roleId}".format(
            courseId=course_id, roleId=role_id
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

    def patch_role(
        self: CourseService[client.AuthenticatedClient],
        json_body: PatchRoleCourseData,
        *,
        course_id: int,
        role_id: int,
    ) -> ExtendedCourseRole:
        """Update the `Permission` of a given `CourseRole` in the given
        `Course`.

        :param json_body: The body of the request. See
            :class:`.PatchRoleCourseData` for information about the possible
            fields. You can provide this data as a
            :class:`.PatchRoleCourseData` or as a dictionary.
        :param course_id: The id of the course.
        :param role_id: The id of the course role.

        :returns: An empty response with return code 204.
        """

        url = "/api/v1/courses/{courseId}/roles/{roleId}".format(
            courseId=course_id, roleId=role_id
        )
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_course_role import ExtendedCourseRole

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedCourseRole)
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

    def delete_user(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        user_id: int,
    ) -> None:
        """Delete a user from a course.

        This does not delete the user's submissions within the course.

        :param course_id: The id of the course to remove the user from.
        :param user_id: The id of the user to remove from the course.

        :returns: Nothing.
        """

        url = "/api/v1/courses/{courseId}/users/{userId}".format(
            courseId=course_id, userId=user_id
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

    def get_all_users(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        q: str = "",
        page_size: int = 20,
    ) -> paginated.Response[CourseEnrollment]:
        """Get all users and their role in a course.

        :param course_id: The id of the course
        :param q: Only retrieve users whose name or username matches this
                  value. This will change the output to a list of users.
        :param page_size: The size of a single page, maximum is 50.

        :returns: All users in this course and their role.
        """

        url = "/api/v1/courses/{courseId}/enrollments/".format(
            courseId=course_id
        )
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

        def parse_response(
            resp: httpx.Response,
        ) -> t.Sequence[CourseEnrollment]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.course_enrollment import CourseEnrollment

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(CourseEnrollment))
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

    def change_user_role(
        self: CourseService[client.AuthenticatedClient],
        json_body: ChangeUserRoleCourseData,
        *,
        course_id: int,
    ) -> CourseEnrollment:
        """Set the `CourseRole` of a user in the given course.

        :param json_body: The body of the request. See
            :class:`.ChangeUserRoleCourseData` for information about the
            possible fields. You can provide this data as a
            :class:`.ChangeUserRoleCourseData` or as a dictionary.
        :param course_id: The id of the course in which you want to enroll a
            new user, or change the role of an existing user.

        :returns: The response will contain the JSON serialized user and course
                  role.
        """

        url = "/api/v1/courses/{courseId}/enrollments/".format(
            courseId=course_id
        )
        params = None

        with self.__client as client:
            resp = client.http.put(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.course_enrollment import CourseEnrollment

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(CourseEnrollment)
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
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
    ) -> ExtendedCourse:
        """Get a course by id.

        :param course_id: The id of the course

        :returns: A response containing the JSON serialized course
        """

        url = "/api/v1/courses/{courseId}".format(courseId=course_id)
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_course import ExtendedCourse

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedCourse)
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
        self: CourseService[client.AuthenticatedClient],
        json_body: PatchCourseData,
        *,
        course_id: int,
    ) -> ExtendedCourse:
        """Update the given course with new values.

        :param json_body: The body of the request. See
            :class:`.PatchCourseData` for information about the possible
            fields. You can provide this data as a :class:`.PatchCourseData` or
            as a dictionary.
        :param course_id: The id of the course you want to update.

        :returns: The updated course, in extended format.
        """

        url = "/api/v1/courses/{courseId}".format(courseId=course_id)
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_course import ExtendedCourse

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedCourse)
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

    def get_snippets(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        page_size: int = 20,
    ) -> paginated.Response[CourseSnippet]:
        """Get all snippets of the given course.

        :param course_id: The id of the course from which you want to get the
            snippets.
        :param page_size: The size of a single page, maximum is 50.

        :returns: An array containing all snippets for the given course.
        """

        url = "/api/v1/courses/{courseId}/snippets/".format(courseId=course_id)
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

        def parse_response(resp: httpx.Response) -> t.Sequence[CourseSnippet]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.course_snippet import CourseSnippet

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(CourseSnippet))
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

    def get_statistics(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
    ) -> CourseStatisticsAsJSON:
        """Get user statistics of a specific course.

        :param course_id: The id of the course for which you want to get the
            statistics

        :returns: A response containing the course management statistics
        """

        url = "/api/v1/courses/{courseId}/statistics".format(
            courseId=course_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.course_statistics_as_json import (
                CourseStatisticsAsJSON,
            )

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(CourseStatisticsAsJSON)
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

    def get_authorization(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
    ) -> CourseAuthorization:
        """Get all the authorization of the currently logged in user in this
        course.

        This will return the permission as if you have already paid, even if
        this is not the case. We will also not check any restrictions of the
        current session.

        :param course_id: The id of the course of which the permissions should
            be retrieved.

        :returns: A mapping between the permission name and a boolean
                  indicating if the currently logged in user has this
                  permission.
        """

        url = "/api/v1/courses/{courseId}/authorization".format(
            courseId=course_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.course_authorization import CourseAuthorization

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(CourseAuthorization)
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

    def get_submissions_by_user(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        user_id: int,
        page_size: int = 20,
    ) -> paginated.Response[Work]:
        """Get all submissions by the given user in this course.

        :param course_id: The id of the course from which you want to get the
            submissions.
        :param user_id: The id of the user of which you want to get the
            submissions.
        :param page_size: The size of a single page, maximum is 50.

        :returns: A paginated list of the submissions by the user in this
                  course.
        """

        url = "/api/v1/courses/{courseId}/users/{userId}/submissions/".format(
            courseId=course_id, userId=user_id
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

        def parse_response(resp: httpx.Response) -> t.Sequence[Work]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.work import Work

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(Work))
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

    def import_into(
        self: CourseService[client.AuthenticatedClient],
        json_body: ImportIntoCourseData,
        *,
        into_course_id: int,
    ) -> ExtendedCourse:
        """Copy a course into another course.

        :param json_body: The body of the request. See
            :class:`.ImportIntoCourseData` for information about the possible
            fields. You can provide this data as a
            :class:`.ImportIntoCourseData` or as a dictionary.
        :param into_course_id: The course you want to import into.

        :returns: The updated course, so the course of which the id was passed
                  in the url.
        """

        url = "/api/v1/courses/{intoCourseId}/copy".format(
            intoCourseId=into_course_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_course import ExtendedCourse

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedCourse)
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

    def import_snippets_into(
        self: CourseService[client.AuthenticatedClient],
        json_body: ImportSnippetsIntoCourseData,
        *,
        into_course_id: int,
    ) -> None:
        """Import snippets from another course into this course.

        :param json_body: The body of the request. See
            :class:`.ImportSnippetsIntoCourseData` for information about the
            possible fields. You can provide this data as a
            :class:`.ImportSnippetsIntoCourseData` or as a dictionary.
        :param into_course_id: The course you want to import snippets into.

        :returns: Nothing.
        """

        url = "/api/v1/courses/{intoCourseId}/snippets/import".format(
            intoCourseId=into_course_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(
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

    def join_as_logged_in_user(
        self: CourseService[client.AuthenticatedClient],
        *,
        course_id: int,
        link_id: str,
    ) -> None:
        """Join a course as the currently logged in user using a registration
        link.

        :param course_id: The id of the course in which you want to enroll.
        :param link_id: The id of the link you want to use to enroll.

        :returns: Nothing.
        """

        url = "/api/v1/courses/{courseId}/registration_links/{linkId}/join".format(
            courseId=course_id, linkId=link_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(url=url, params=params)
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

    def register_user_with_link(
        self,
        json_body: RegisterUserWithLinkCourseData,
        *,
        course_id: int,
        link_id: str,
    ) -> UserLoginResponse:
        """Register as a new user, and directly enroll in a course.

        :param json_body: The body of the request. See
            :class:`.RegisterUserWithLinkCourseData` for information about the
            possible fields. You can provide this data as a
            :class:`.RegisterUserWithLinkCourseData` or as a dictionary.
        :param course_id: The id of the course to which the registration link
            is connected.
        :param link_id: The id of the registration link.

        :returns: The access token that the created user can use to log in.
        """

        url = "/api/v1/courses/{courseId}/registration_links/{linkId}/user".format(
            courseId=course_id, linkId=link_id
        )
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

    def email_users(
        self: CourseService[client.AuthenticatedClient],
        json_body: EmailUsersCourseData,
        *,
        course_id: int,
    ) -> Job:
        """Sent the authors in this course an email.

        :param json_body: The body of the request. See
            :class:`.EmailUsersCourseData` for information about the possible
            fields. You can provide this data as a
            :class:`.EmailUsersCourseData` or as a dictionary.
        :param course_id: The id of the course in which you want to send the
            emails.

        :returns: A task result that will send these emails.
        """

        url = "/api/v1/courses/{courseId}/email".format(courseId=course_id)
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.job import Job

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(Job)
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
