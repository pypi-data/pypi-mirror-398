"""The endpoints for assignment objects.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import os
import typing as t

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from .. import paginated, parsers, utils
from ..models.ignore_handling import IgnoreHandling

if t.TYPE_CHECKING or os.getenv("CG_EAGERIMPORT", False):
    from .. import client
    from ..models.analytics_data import AnalyticsData
    from ..models.assignment_gradebook_row import AssignmentGradebookRow
    from ..models.assignment_grader import AssignmentGrader
    from ..models.assignment_ip_range import AssignmentIPRange
    from ..models.assignment_password_response import (
        AssignmentPasswordResponse,
    )
    from ..models.assignment_peer_feedback_connection import (
        AssignmentPeerFeedbackConnection,
    )
    from ..models.assignment_peer_feedback_settings import (
        AssignmentPeerFeedbackSettings,
    )
    from ..models.assignment_timeframes import AssignmentTimeframes
    from ..models.auto_test import AutoTest
    from ..models.copy_rubric_assignment_data import CopyRubricAssignmentData
    from ..models.create_plagiarism_run_assignment_data import (
        CreatePlagiarismRunAssignmentData,
    )
    from ..models.divide_graders_assignment_data import (
        DivideGradersAssignmentData,
    )
    from ..models.export_assignment_data import ExportAssignmentData
    from ..models.extended_assignment import ExtendedAssignment
    from ..models.extended_assignment_template import (
        ExtendedAssignmentTemplate,
    )
    from ..models.extended_work import ExtendedWork
    from ..models.import_into_assignment_data import ImportIntoAssignmentData
    from ..models.job import Job
    from ..models.patch_assignment_data import PatchAssignmentData
    from ..models.patch_rubric_category_type_assignment_data import (
        PatchRubricCategoryTypeAssignmentData,
    )
    from ..models.patch_submit_types_assignment_data import (
        PatchSubmitTypesAssignmentData,
    )
    from ..models.plagiarism_run import PlagiarismRun
    from ..models.put_description_assignment_data import (
        PutDescriptionAssignmentData,
    )
    from ..models.put_division_parent_assignment_data import (
        PutDivisionParentAssignmentData,
    )
    from ..models.put_password_assignment_data import PutPasswordAssignmentData
    from ..models.put_rubric_assignment_data import PutRubricAssignmentData
    from ..models.rubric_row_base import RubricRowBase
    from ..models.update_peer_feedback_settings_assignment_data import (
        UpdatePeerFeedbackSettingsAssignmentData,
    )
    from ..models.upload_submission_assignment_data import (
        UploadSubmissionAssignmentData,
    )
    from ..models.user_login_response import UserLoginResponse
    from ..models.verify_assignment_data import VerifyAssignmentData
    from ..models.webhook_base import WebhookBase
    from ..models.work import Work
    from ..models.work_comment_count import WorkCommentCount


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class AssignmentService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_rubric(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        page_size: int = 50,
    ) -> paginated.Response[RubricRowBase]:
        """Return the rubric corresponding to the given `assignment_id`.

        :param assignment_id: The id of the assignment.
        :param page_size: The size of a single page, maximum is 100.

        :returns: A list of `RubricRow` items.
        """

        url = "/api/v1/assignments/{assignmentId}/rubrics/".format(
            assignmentId=assignment_id
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

        def parse_response(resp: httpx.Response) -> t.Sequence[RubricRowBase]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.rubric_row_base import RubricRowBase

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(RubricRowBase))
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

    def put_rubric(
        self: AssignmentService[client.AuthenticatedClient],
        json_body: PutRubricAssignmentData,
        *,
        assignment_id: int,
    ) -> t.Sequence[RubricRowBase]:
        """Add or update rubric of an assignment.

        :param json_body: The body of the request. See
            :class:`.PutRubricAssignmentData` for information about the
            possible fields. You can provide this data as a
            :class:`.PutRubricAssignmentData` or as a dictionary.
        :param assignment_id: The id of the assignment

        :returns: The updated or created rubric.
        """

        url = "/api/v1/assignments/{assignmentId}/rubrics/".format(
            assignmentId=assignment_id
        )
        params = None

        with self.__client as client:
            resp = client.http.put(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.rubric_row_base import RubricRowBase

            return parsers.JsonResponseParser(
                rqa.List(parsers.ParserFor.make(RubricRowBase))
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

    def delete_rubric(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
    ) -> None:
        """Delete the rubric for the given assignment.

        :param assignment_id: The id of the `Assignment` whose rubric should be
            deleted.

        :returns: Nothing.
        """

        url = "/api/v1/assignments/{assignmentId}/rubrics/".format(
            assignmentId=assignment_id
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

    def put_division_parent(
        self: AssignmentService[client.AuthenticatedClient],
        json_body: PutDivisionParentAssignmentData,
        *,
        assignment_id: int,
    ) -> None:
        """Change the division parent of an assignment.

        Set the division parent of this assignment. See the documentation about
        dividing submissions for more information about division parents.

        :param json_body: The body of the request. See
            :class:`.PutDivisionParentAssignmentData` for information about the
            possible fields. You can provide this data as a
            :class:`.PutDivisionParentAssignmentData` or as a dictionary.
        :param assignment_id: The id of the assignment you want to change.

        :returns: An empty response with status code code 204.
        """

        url = "/api/v1/assignments/{assignmentId}/division_parent".format(
            assignmentId=assignment_id
        )
        params = None

        with self.__client as client:
            resp = client.http.put(
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

    def patch_rubric_category_type(
        self: AssignmentService[client.AuthenticatedClient],
        json_body: PatchRubricCategoryTypeAssignmentData,
        *,
        assignment_id: int,
        rubric_category_id: int,
    ) -> RubricRowBase:
        """Change the type of a rubric category.

        :param json_body: The body of the request. See
            :class:`.PatchRubricCategoryTypeAssignmentData` for information
            about the possible fields. You can provide this data as a
            :class:`.PatchRubricCategoryTypeAssignmentData` or as a dictionary.
        :param assignment_id: The assignment of the rubric category.
        :param rubric_category_id: The rubric category you want to change the
            type of.

        :returns: The updated rubric row.
        """

        url = "/api/v1/assignments/{assignmentId}/rubrics/{rubricCategoryId}/type".format(
            assignmentId=assignment_id, rubricCategoryId=rubric_category_id
        )
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.rubric_row_base import RubricRowBase

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(RubricRowBase)
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
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
    ) -> ExtendedAssignment:
        """Get a single assignment by id.

        :param assignment_id: The id of the assignment you want to get.

        :returns: The requested assignment.
        """

        url = "/api/v1/assignments/{assignmentId}".format(
            assignmentId=assignment_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
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

    def delete(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
    ) -> None:
        """Delete a given `Assignment`.

        :param assignment_id: The id of the assignment

        :returns: Nothing.
        """

        url = "/api/v1/assignments/{assignmentId}".format(
            assignmentId=assignment_id
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

    def patch(
        self: AssignmentService[client.AuthenticatedClient],
        json_body: PatchAssignmentData,
        *,
        assignment_id: int,
    ) -> ExtendedAssignment:
        """Update the given assignment with new values.

        :param json_body: The body of the request. See
            :class:`.PatchAssignmentData` for information about the possible
            fields. You can provide this data as a
            :class:`.PatchAssignmentData` or as a dictionary.
        :param assignment_id: The id of the assignment you want to update.

        :returns: The updated assignment.
        """

        url = "/api/v1/assignments/{assignmentId}".format(
            assignmentId=assignment_id
        )
        params = None

        with self.__client as client:
            resp = client.http.patch(
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

    def get_description(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
    ) -> bytes:
        """Get the description for this assignment.

        :param assignment_id: The id of the assignment;

        :returns: A public link that allows users to download the file or the
                  file itself as a stream of octets
        """

        url = "/api/v1/assignments/{assignmentId}/description".format(
            assignmentId=assignment_id
        )
        params = None

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

    def put_description(
        self: AssignmentService[client.AuthenticatedClient],
        multipart_data: PutDescriptionAssignmentData,
        *,
        assignment_id: int,
    ) -> None:
        """Stores a file containing the new description for a given
        `Assignment`.

        :param multipart_data: The data that should form the body of the
            request. See :class:`.PutDescriptionAssignmentData` for information
            about the possible fields.
        :param assignment_id: The id of the assignment

        :returns: An empty response.
        """

        url = "/api/v1/assignments/{assignmentId}/description".format(
            assignmentId=assignment_id
        )
        params = None

        data, files = utils.to_multipart(utils.to_dict(multipart_data))

        with self.__client as client:
            resp = client.http.put(
                url=url, files=files, data=data, params=params
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

    def delete_description(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
    ) -> None:
        """Deletes the description for a given `Assignment`.

        :param assignment_id: The id of the assignment.

        :returns: An empty response.
        """

        url = "/api/v1/assignments/{assignmentId}/description".format(
            assignmentId=assignment_id
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

    def get_password(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
    ) -> AssignmentPasswordResponse:
        """Get the password for an assignment (admin only).

        :param assignment_id: The id of the assignment.

        :returns: JSON response with password or null.
        """

        url = "/api/v1/assignments/{assignmentId}/password".format(
            assignmentId=assignment_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.assignment_password_response import (
                AssignmentPasswordResponse,
            )

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(AssignmentPasswordResponse)
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

    def put_password(
        self: AssignmentService[client.AuthenticatedClient],
        json_body: PutPasswordAssignmentData,
        *,
        assignment_id: int,
    ) -> AssignmentPasswordResponse:
        """Set the password for an assignment.

        :param json_body: The body of the request. See
            :class:`.PutPasswordAssignmentData` for information about the
            possible fields. You can provide this data as a
            :class:`.PutPasswordAssignmentData` or as a dictionary.
        :param assignment_id: The id of the assignment.

        :returns: An empty response.
        """

        url = "/api/v1/assignments/{assignmentId}/password".format(
            assignmentId=assignment_id
        )
        params = None

        with self.__client as client:
            resp = client.http.put(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.assignment_password_response import (
                AssignmentPasswordResponse,
            )

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(AssignmentPasswordResponse)
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

    def delete_password(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
    ) -> None:
        """Remove password protection from an assignment.

        :param assignment_id: The id of the assignment.

        :returns: An empty response.
        """

        url = "/api/v1/assignments/{assignmentId}/password".format(
            assignmentId=assignment_id
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

    def get_template(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
    ) -> ExtendedAssignmentTemplate:
        """Return the template corresponding to the given `assignment_id`.

        :param assignment_id: The id of the assignment.

        :returns: The template for this assignment.
        """

        url = "/api/v1/assignments/{assignmentId}/template".format(
            assignmentId=assignment_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_assignment_template import (
                ExtendedAssignmentTemplate,
            )

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedAssignmentTemplate)
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

    def delete_template(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
    ) -> None:
        """Delete the template corresponding to the given `assignment_id`.

        :param assignment_id: The id of the assignment.

        :returns: Nothing.
        """

        url = "/api/v1/assignments/{assignmentId}/template".format(
            assignmentId=assignment_id
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

    def put_allowed_ip(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        ip_range: str,
    ) -> AssignmentIPRange:
        """Add a single IP range lock to an assignment.

        :param assignment_id: The id of the assignment.
        :param ip_range: The ip range you want to add.

        :returns: A JSON response returning the added item.
        """

        url = (
            "/api/v1/assignments/{assignmentId}/allowed_ips/{ipRange}".format(
                assignmentId=assignment_id, ipRange=ip_range
            )
        )
        params = None

        with self.__client as client:
            resp = client.http.put(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.assignment_ip_range import AssignmentIPRange

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(AssignmentIPRange)
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

    def delete_allowed_ip(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        ip_range: str,
    ) -> None:
        """Delete a single IP range lock from an assignment by ID.

        :param assignment_id: The ID of the assignment.
        :param ip_range: The IP range (or single IP).

        :returns: An empty response.
        """

        url = (
            "/api/v1/assignments/{assignmentId}/allowed_ips/{ipRange}".format(
                assignmentId=assignment_id, ipRange=ip_range
            )
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

    def update_peer_feedback_settings(
        self: AssignmentService[client.AuthenticatedClient],
        json_body: UpdatePeerFeedbackSettingsAssignmentData,
        *,
        assignment_id: int,
    ) -> AssignmentPeerFeedbackSettings:
        """Enable peer feedback for an assignment.

        :param json_body: The body of the request. See
            :class:`.UpdatePeerFeedbackSettingsAssignmentData` for information
            about the possible fields. You can provide this data as a
            :class:`.UpdatePeerFeedbackSettingsAssignmentData` or as a
            dictionary.
        :param assignment_id: The id of the assignment for which you want to
            enable peer feedback.

        :returns: The just created peer feedback settings.
        """

        url = (
            "/api/v1/assignments/{assignmentId}/peer_feedback_settings".format(
                assignmentId=assignment_id
            )
        )
        params = None

        with self.__client as client:
            resp = client.http.put(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.assignment_peer_feedback_settings import (
                AssignmentPeerFeedbackSettings,
            )

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(AssignmentPeerFeedbackSettings)
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

    def disable_peer_feedback(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
    ) -> None:
        """Disabled peer feedback for an assignment.

        :param assignment_id: The id of the assignment for which you want to
            disable peer feedback.

        :returns: Nothing; an empty response.
        """

        url = (
            "/api/v1/assignments/{assignmentId}/peer_feedback_settings".format(
                assignmentId=assignment_id
            )
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

    def divide_graders(
        self: AssignmentService[client.AuthenticatedClient],
        json_body: DivideGradersAssignmentData,
        *,
        assignment_id: int,
    ) -> None:
        """Assign graders to all the latest :class:.models.Work objects of the
        given :class:.models.Assignment.

        The redivide tries to minimize shuffles. This means that calling it
        twice with the same data is effectively a noop. If the relative weight
        (so the percentage of work) of a user doesn't change it will not lose
        or gain any submissions.

        If a user was marked as done grading and gets assigned new submissions
        this user is marked as not done and gets a notification email!

        :param json_body: The body of the request. See
            :class:`.DivideGradersAssignmentData` for information about the
            possible fields. You can provide this data as a
            :class:`.DivideGradersAssignmentData` or as a dictionary.
        :param assignment_id: The id of the assignment

        :returns: An empty response with return code 204
        """

        url = "/api/v1/assignments/{assignmentId}/grader_division".format(
            assignmentId=assignment_id
        )
        params = None

        with self.__client as client:
            resp = client.http.put(
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

    def export(
        self: AssignmentService[client.AuthenticatedClient],
        json_body: ExportAssignmentData,
        *,
        assignment_id: int,
    ) -> Job:
        """Generate a CSV report for this assignment.

        :param json_body: The body of the request. See
            :class:`.ExportAssignmentData` for information about the possible
            fields. You can provide this data as a
            :class:`.ExportAssignmentData` or as a dictionary.
        :param assignment_id: The id of the assignment

        :returns: A CSV report for this assignment.
        """

        url = "/api/v1/assignments/{assignmentId}/export".format(
            assignmentId=assignment_id
        )
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

    def get_all_grades(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        page_size: int = 150,
    ) -> paginated.Response[AssignmentGradebookRow]:
        """Get the grades for all submissions in this assignment.

        :param assignment_id: The id of assignment to export the gradebook for.
        :param page_size: The size of a single page, maximum is 200.

        :returns: The rows of the gradebook.
        """

        url = "/api/v1/assignments/{assignmentId}/grades/".format(
            assignmentId=assignment_id
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
        ) -> t.Sequence[AssignmentGradebookRow]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.assignment_gradebook_row import (
                    AssignmentGradebookRow,
                )

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(AssignmentGradebookRow))
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

    def get_all_graders(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        page_size: int = 20,
    ) -> paginated.Response[AssignmentGrader]:
        """Gets a list of all users that can grade in the given assignment.

        :param assignment_id: The id of the assignment
        :param page_size: The size of a single page, maximum is 50.

        :returns: A response containing the JSON serialized graders.
        """

        url = "/api/v1/assignments/{assignmentId}/graders/".format(
            assignmentId=assignment_id
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
        ) -> t.Sequence[AssignmentGrader]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.assignment_grader import AssignmentGrader

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(AssignmentGrader))
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

    def get_submissions_by_user(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        user_id: int,
        page_size: int = 20,
    ) -> paginated.Response[Work]:
        """Return all submissions by the given user in the given assignment.

        For group assignments this route will also include submissions by the
        group of the user, which are always seen as later than the submission
        of the user.

        :param assignment_id: The id of the assignment
        :param user_id: The user of which you want to get the submissions.
        :param page_size: The size of a single page, maximum is 50.

        :returns: A response containing the JSON serialized submissions.
        """

        url = "/api/v1/assignments/{assignmentId}/users/{userId}/submissions/".format(
            assignmentId=assignment_id, userId=user_id
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

    def get_all_submissions(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        q: str = "",
        test_student: Maybe[bool] = Nothing,
        page_size: int = 50,
    ) -> paginated.Response[Work]:
        """Return all submissions for the given assignment.

        :param assignment_id: The id of the assignment
        :param q: Filter the submissions returned based on this string.
        :param test_student: If give only return submissions that either are or
            are not of the test student.
        :param page_size: The size of a single page, maximum is 100.

        :returns: A response containing the JSON serialized submissions.
        """

        url = "/api/v1/assignments/{assignmentId}/submissions/".format(
            assignmentId=assignment_id
        )
        params: t.Dict[str, str | int | bool] = {
            "q": q,
            "page-size": page_size,
        }
        test_student_as_maybe = maybe_from_nullable(test_student)
        if test_student_as_maybe.is_just:
            params["test_student"] = test_student_as_maybe.value

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

    def get_analytics_data(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        data_source_name: str,
        page_size: int = 100,
    ) -> paginated.Response[AnalyticsData]:
        """Get the data of an analytics source.

        the data. the data.

        :param assignment_id: The id of the assignment from which you want to
            get the data.
        :param data_source_name: The name of the data source of which you wan
            to get the data.
        :param page_size: The size of a single page, maximum is 250.

        :returns: A paginated list of the data.
        """

        url = "/api/v1/assignments/{assignmentId}/analytics/{dataSourceName}/data/".format(
            assignmentId=assignment_id, dataSourceName=data_source_name
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

        def parse_response(resp: httpx.Response) -> t.Sequence[AnalyticsData]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.analytics_data import AnalyticsData

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(AnalyticsData))
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

    def get_all_allowed_ips(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        page_size: int = 50,
    ) -> paginated.Response[AssignmentIPRange]:
        """Get all IP ranges for an assignment.

        :param assignment_id: The ID of the assignment.
        :param page_size: The size of a single page, maximum is 100.

        :returns: A JSON response containing the list of IP ranges.
        """

        url = "/api/v1/assignments/{assignmentId}/allowed_ips/".format(
            assignmentId=assignment_id
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
        ) -> t.Sequence[AssignmentIPRange]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.assignment_ip_range import AssignmentIPRange

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(AssignmentIPRange))
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

    def get_template_file(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        file_id: str,
    ) -> bytes:
        """Get the content of a single file of an assignment template.

        :param assignment_id: The id of the assignment.
        :param file_id: The id of the file.

        :returns: The contents of the requested file.
        """

        url = "/api/v1/assignments/{assignmentId}/template/{fileId}".format(
            assignmentId=assignment_id, fileId=file_id
        )
        params = None

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

    def get_timeframes(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
    ) -> AssignmentTimeframes:
        """Get the schedule for the specified `Assignment`.

        :param assignment_id: The id of the assignment;

        :returns: The assignment schedule.
        """

        url = "/api/v1/assignments/{assignmentId}/timeframes/".format(
            assignmentId=assignment_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.assignment_timeframes import AssignmentTimeframes

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(AssignmentTimeframes)
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

    def put_timeframes(
        self: AssignmentService[client.AuthenticatedClient],
        json_body: AssignmentTimeframes,
        *,
        assignment_id: int,
    ) -> AssignmentTimeframes:
        """Updates the schedule for the specified `Assignment`.

        :param json_body: The body of the request. See
            :class:`.AssignmentTimeframes` for information about the possible
            fields. You can provide this data as a
            :class:`.AssignmentTimeframes` or as a dictionary.
        :param assignment_id: The id of the assignment;

        :returns: The updated assignment schedule.
        """

        url = "/api/v1/assignments/{assignmentId}/timeframes/".format(
            assignmentId=assignment_id
        )
        params = None

        with self.__client as client:
            resp = client.http.put(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.assignment_timeframes import AssignmentTimeframes

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(AssignmentTimeframes)
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

    def get_auto_test(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
    ) -> AutoTest:
        """Get the `AutoTest` for this assignment.

        :param assignment_id: The id of the assignment from which you want to
            get the `AutoTest`.

        :returns: The `AutoTest` for the given assignment, if it has an
                  `AutoTest`.
        """

        url = "/api/v1/assignments/{assignmentId}/auto_test".format(
            assignmentId=assignment_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.auto_test import AutoTest

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(AutoTest)
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

    def get_webhook_settings(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        webhook_type: t.Literal["git"],
        author_id: Maybe[int] = Nothing,
        is_test_submission: bool = False,
    ) -> WebhookBase:
        """Create or get the webhook settings to hand-in submissions.

        You can select the user for which the webhook should hand-in using the
        exact same query parameters as the route to upload a submission.

        :param assignment_id: The assignment for which the webhook should
            hand-in submissions.
        :param webhook_type: The webhook type, currently only `git` is
            supported, which works for both GitLab and GitHub.
        :param author_id: The id of the user for which we should get the
            webhook settings. If not given defaults to the current user.
        :param is_test_submission: Should we get the webhook settings for the
            test student.

        :returns: A serialized form of a webhook, which contains all data
                  needed to add the webhook to your provider.
        """

        url = "/api/v1/assignments/{assignmentId}/webhook_settings".format(
            assignmentId=assignment_id
        )
        params: t.Dict[str, str | int | bool] = {
            "webhook_type": webhook_type,
            "is_test_submission": is_test_submission,
        }
        author_id_as_maybe = maybe_from_nullable(author_id)
        if author_id_as_maybe.is_just:
            params["author_id"] = author_id_as_maybe.value

        with self.__client as client:
            resp = client.http.post(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.webhook_base import WebhookBase

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(WebhookBase)
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

    def get_next_ungraded_submission(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        current_submission_id: Maybe[int] = Nothing,
    ) -> ExtendedWork:
        """Get the next ungraded submission for the given assignment.

        Returns the next ungraded submission assigned in the following order:
        1. Those belonging to the current grader. 2. Those assigned to no
        grader. If no more ungraded submissions exist it returns 404.

        :param assignment_id: The id of the assignment.
        :param current_submission_id: The id of the submission to exclude in
            the search.

        :returns: The next ungraded submission that should be graded by the
                  user.
        """

        url = "/api/v1/assignments/{assignmentId}/next-ungraded-submission".format(
            assignmentId=assignment_id
        )
        params: t.Dict[str, str | int | bool] = {}
        current_submission_id_as_maybe = maybe_from_nullable(
            current_submission_id
        )
        if current_submission_id_as_maybe.is_just:
            params["current_submission_id"] = (
                current_submission_id_as_maybe.value
            )

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_work import ExtendedWork

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedWork)
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

    def get_peer_feedback_subjects(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        user_id: int,
        page_size: int = 20,
    ) -> paginated.Response[AssignmentPeerFeedbackConnection]:
        """Get the peer feedback subjects for a given user.

        This endpoint retrieves the list of subjects (i.e., other users or
        groups) that the specified user is assigned to review. It transparently
        handles both individual and group assignments.

        :param assignment_id: The ID of the assignment.
        :param user_id: The ID of the user whose peer feedback duties are being
            requested. For group assignments, providing an individual member's
            ID will return the subjects assigned to their entire group.
        :param page_size: The size of a single page, maximum is 50.

        :returns: A paginated list of peer feedback subjects. Returns an empty
                  list if the assignment's feedback period is not active or if
                  it is not a peer feedback assignment.
        """

        url = "/api/v1/assignments/{assignmentId}/users/{userId}/peer_feedback_subjects/".format(
            assignmentId=assignment_id, userId=user_id
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
        ) -> t.Sequence[AssignmentPeerFeedbackConnection]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.assignment_peer_feedback_connection import (
                    AssignmentPeerFeedbackConnection,
                )

                return parsers.JsonResponseParser(
                    rqa.List(
                        parsers.ParserFor.make(
                            AssignmentPeerFeedbackConnection
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

    def get_all_plagiarism_runs(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        q: str = "",
        page_size: int = 20,
    ) -> paginated.Response[PlagiarismRun]:
        """Get all plagiarism runs for the given assignment.

        :param assignment_id: The id of the assignment
        :param q: Search the runs based on this value.
        :param page_size: The size of a single page, maximum is 50.

        :returns: A response containing the JSON serialized list of plagiarism
                  runs.
        """

        url = "/api/v1/assignments/{assignmentId}/plagiarism/".format(
            assignmentId=assignment_id
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

        def parse_response(resp: httpx.Response) -> t.Sequence[PlagiarismRun]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.plagiarism_run import PlagiarismRun

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(PlagiarismRun))
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

    def get_reply_counts_for_user(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        user_id: int,
        page_size: int = 20,
    ) -> paginated.Response[WorkCommentCount]:
        """Retrieves reply counts for a specific user, grouped by submission.

        This endpoint provides an efficient summary of a user's activity within
        an assignment. It's useful for analytics or dashboard views where you
        need to see how many replies a user has contributed to each submission
        without fetching the full comment data.

        :param assignment_id: The ID of the assignment to scope the search to.
        :param user_id: The ID of the user whose replies are being counted.
        :param page_size: The size of a single page, maximum is 50.

        :returns: A paginated response. The data payload is a list of objects,
                  each mapping a submission's ID to the total count of replies
                  the specified user made on it.
        """

        url = "/api/v1/assignments/{assignmentId}/users/{userId}/replies/counts-by-submission/".format(
            assignmentId=assignment_id, userId=user_id
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
        ) -> t.Sequence[WorkCommentCount]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.work_comment_count import WorkCommentCount

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(WorkCommentCount))
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
        self: AssignmentService[client.AuthenticatedClient],
        json_body: ImportIntoAssignmentData,
        *,
        into_assignment_id: int,
    ) -> ExtendedAssignment:
        """Import an assignment into another assignment.

        :param json_body: The body of the request. See
            :class:`.ImportIntoAssignmentData` for information about the
            possible fields. You can provide this data as a
            :class:`.ImportIntoAssignmentData` or as a dictionary.
        :param into_assignment_id: The assignment you want to import into.

        :returns: The updated assignment, so the assignment which was imported
                  into.
        """

        url = "/api/v1/assignments/{intoAssignmentId}/import".format(
            intoAssignmentId=into_assignment_id
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

    def copy_rubric(
        self: AssignmentService[client.AuthenticatedClient],
        json_body: CopyRubricAssignmentData,
        *,
        assignment_id: int,
    ) -> t.Sequence[RubricRowBase]:
        """Import a rubric from a different assignment.

        :param json_body: The body of the request. See
            :class:`.CopyRubricAssignmentData` for information about the
            possible fields. You can provide this data as a
            :class:`.CopyRubricAssignmentData` or as a dictionary.
        :param assignment_id: The id of the assignment in which you want to
            import the rubric. This assignment shouldn't have a rubric.

        :returns: The rubric rows of the assignment in which the rubric was
                  imported, so the assignment with id `assignment_id` and not
                  `old_assignment_id`.
        """

        url = "/api/v1/assignments/{assignmentId}/rubric".format(
            assignmentId=assignment_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.rubric_row_base import RubricRowBase

            return parsers.JsonResponseParser(
                rqa.List(parsers.ParserFor.make(RubricRowBase))
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

    def mark_grader_as_done(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        grader_id: int,
    ) -> None:
        """Indicate that the given grader is done grading the given assignment.

        :param assignment_id: The id of the assignment the grader is done
            grading.
        :param grader_id: The id of the `User` that is done grading.

        :returns: An empty response with return code 204
        """

        url = "/api/v1/assignments/{assignmentId}/graders/{graderId}/done".format(
            assignmentId=assignment_id, graderId=grader_id
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

    def mark_grader_as_not_done(
        self: AssignmentService[client.AuthenticatedClient],
        *,
        assignment_id: int,
        grader_id: int,
    ) -> None:
        """Indicate that the given grader is not yet done grading the given
        assignment.

        :param assignment_id: The id of the assignment the grader is not yet
            done grading.
        :param grader_id: The id of the `User` that is not yet done grading.

        :returns: An empty response with return code 204
        """

        url = "/api/v1/assignments/{assignmentId}/graders/{graderId}/done".format(
            assignmentId=assignment_id, graderId=grader_id
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

    def create_plagiarism_run(
        self: AssignmentService[client.AuthenticatedClient],
        multipart_data: CreatePlagiarismRunAssignmentData,
        *,
        assignment_id: int,
    ) -> PlagiarismRun:
        """Run a plagiarism checker for the given `Assignment`.

        :param multipart_data: The data that should form the body of the
            request. See :class:`.CreatePlagiarismRunAssignmentData` for
            information about the possible fields.
        :param assignment_id: The id of the assignment

        :returns: The json serialization newly created
        """

        url = "/api/v1/assignments/{assignmentId}/plagiarism".format(
            assignmentId=assignment_id
        )
        params = None

        data, files = utils.to_multipart(utils.to_dict(multipart_data))

        with self.__client as client:
            resp = client.http.post(
                url=url, files=files, data=data, params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.plagiarism_run import PlagiarismRun

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(PlagiarismRun)
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

    def patch_submit_types(
        self: AssignmentService[client.AuthenticatedClient],
        multipart_data: PatchSubmitTypesAssignmentData,
        *,
        assignment_id: int,
    ) -> ExtendedAssignment:
        """Update the given assignment editor template with new files.

        How this route deals with existing editor templates when submitting is
        still experimental and might change in an upcoming release.

        :param multipart_data: The data that should form the body of the
            request. See :class:`.PatchSubmitTypesAssignmentData` for
            information about the possible fields.
        :param assignment_id: The id of the assignment for which you want to
            update the editor template.

        :returns: The updated assignment.
        """

        url = "/api/v1/assignments/{assignmentId}/submit_types".format(
            assignmentId=assignment_id
        )
        params = None

        data, files = utils.to_multipart(utils.to_dict(multipart_data))

        with self.__client as client:
            resp = client.http.patch(
                url=url, files=files, data=data, params=params
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

    def upload_submission(
        self: AssignmentService[client.AuthenticatedClient],
        multipart_data: UploadSubmissionAssignmentData,
        *,
        assignment_id: int,
        author_id: Maybe[int] = Nothing,
        is_test_submission: bool = False,
        ignored_files: IgnoreHandling = IgnoreHandling.keep,
    ) -> ExtendedWork:
        """Upload one or more files as `Work` to the given `Assignment`.

        :param multipart_data: The data that should form the body of the
            request. See :class:`.UploadSubmissionAssignmentData` for
            information about the possible fields.
        :param assignment_id: The id of the assignment
        :param author_id: The id of the user for which we should get the
            webhook settings. If not given defaults to the current user.
        :param is_test_submission: Should we get the webhook settings for the
            test student.
        :param ignored_files: How to handle ignored files. The options are:
            `keep`: this the default, sipmly do nothing about ignored files.
            `delete`: delete the ignored files. `error`: return an error when
            there are ignored files in the archive.

        :returns: The created work.
        """

        url = "/api/v1/assignments/{assignmentId}/submission".format(
            assignmentId=assignment_id
        )
        params: t.Dict[str, str | int | bool] = {
            "is_test_submission": is_test_submission,
            "ignored_files": ignored_files,
        }
        author_id_as_maybe = maybe_from_nullable(author_id)
        if author_id_as_maybe.is_just:
            params["author_id"] = author_id_as_maybe.value

        data, files = utils.to_multipart(utils.to_dict(multipart_data))

        with self.__client as client:
            resp = client.http.post(
                url=url, files=files, data=data, params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_work import ExtendedWork

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedWork)
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

    def verify(
        self: AssignmentService[client.AuthenticatedClient],
        json_body: VerifyAssignmentData,
        *,
        assignment_id: int,
    ) -> UserLoginResponse:
        """Verify a password for an assignment.

        :param json_body: The body of the request. See
            :class:`.VerifyAssignmentData` for information about the possible
            fields. You can provide this data as a
            :class:`.VerifyAssignmentData` or as a dictionary.
        :param assignment_id: The id of the assignment.

        :returns: An empty response if valid, error if invalid.
        """

        url = "/api/v1/assignments/{assignmentId}/verify".format(
            assignmentId=assignment_id
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
