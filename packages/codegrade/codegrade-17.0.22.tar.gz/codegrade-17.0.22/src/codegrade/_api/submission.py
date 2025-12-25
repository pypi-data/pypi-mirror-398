"""The endpoints for submission objects.

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
    from ..models.create_proxy_submission_data import CreateProxySubmissionData
    from ..models.extended_work import ExtendedWork
    from ..models.feedback_with_replies import FeedbackWithReplies
    from ..models.feedback_without_replies import FeedbackWithoutReplies
    from ..models.grade_history import GradeHistory
    from ..models.mirror_file_result import MirrorFileResult
    from ..models.patch_grader_submission_data import PatchGraderSubmissionData
    from ..models.patch_rubric_result_response import PatchRubricResultResponse
    from ..models.patch_submission_data import PatchSubmissionData
    from ..models.proxy import Proxy
    from ..models.put_rubric_result_submission_data import (
        PutRubricResultSubmissionData,
    )
    from ..models.root_file_trees_json import RootFileTreesJSON
    from ..models.work_rubric_item import WorkRubricItem


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class SubmissionService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def create_proxy(
        self: SubmissionService[client.AuthenticatedClient],
        json_body: CreateProxySubmissionData,
        *,
        submission_id: int,
    ) -> Proxy:
        """Create a proxy to view the files of the given submission through.

        This allows you to view files of a submission without authentication
        for a limited time.

        :param json_body: The body of the request. See
            :class:`.CreateProxySubmissionData` for information about the
            possible fields. You can provide this data as a
            :class:`.CreateProxySubmissionData` or as a dictionary.
        :param submission_id: The submission for which the proxy should be
            created.

        :returns: The created proxy.
        """

        url = "/api/v1/submissions/{submissionId}/proxy".format(
            submissionId=submission_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.proxy import Proxy

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(Proxy)
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
        self: SubmissionService[client.AuthenticatedClient],
        *,
        submission_id: int,
        type: t.Literal["default", "feedback", "zip"] = "default",
        owner: t.Literal["auto", "student", "teacher"] = "auto",
    ) -> t.Union[ExtendedWork, MirrorFileResult]:
        """Get the given submission (also called work) by id.

        :param submission_id: The id of the submission
        :param type: If passed this cause you not to receive a submission
            object. What you will receive will depend on the value passed. If
            you pass `zip` you will receive a zip file with all the files of
            the submission. If you pass `feedback` you will receive a text file
            with a textual representation of all the feedback given on this
            submission.
        :param owner: This query parameter is only used when `type=='zip'`. It
            will determine which revision is used to generate the zip file.

        :returns: The requested submission, or one of the other types as
                  requested by the `type` query parameter.
        """

        url = "/api/v1/submissions/{submissionId}".format(
            submissionId=submission_id
        )
        params: t.Dict[str, str | int | bool] = {
            "type": type,
            "owner": owner,
        }

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_work import ExtendedWork
            from ..models.mirror_file_result import MirrorFileResult

            return parsers.JsonResponseParser(
                parsers.make_union(
                    parsers.ParserFor.make(ExtendedWork),
                    parsers.ParserFor.make(MirrorFileResult),
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

    def delete(
        self: SubmissionService[client.AuthenticatedClient],
        *,
        submission_id: int,
    ) -> None:
        """Delete a submission and all its files.

        :param submission_id: The submission to delete.

        :returns: Nothing
        """

        url = "/api/v1/submissions/{submissionId}".format(
            submissionId=submission_id
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
        self: SubmissionService[client.AuthenticatedClient],
        json_body: PatchSubmissionData,
        *,
        submission_id: int,
    ) -> ExtendedWork:
        """Update the given submission with new values.

        :param json_body: The body of the request. See
            :class:`.PatchSubmissionData` for information about the possible
            fields. You can provide this data as a
            :class:`.PatchSubmissionData` or as a dictionary.
        :param submission_id: The id of the submission.

        :returns: The updated submission.
        """

        url = "/api/v1/submissions/{submissionId}".format(
            submissionId=submission_id
        )
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
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

    def delete_grader(
        self: SubmissionService[client.AuthenticatedClient],
        *,
        submission_id: int,
    ) -> None:
        """Change the assigned grader of the given submission.

        :param submission_id: The id of the submission.

        :returns: Empty response and a 204 status.
        """

        url = "/api/v1/submissions/{submissionId}/grader".format(
            submissionId=submission_id
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

    def patch_grader(
        self: SubmissionService[client.AuthenticatedClient],
        json_body: PatchGraderSubmissionData,
        *,
        submission_id: int,
    ) -> None:
        """Change the assigned grader of the given submission.

        :param json_body: The body of the request. See
            :class:`.PatchGraderSubmissionData` for information about the
            possible fields. You can provide this data as a
            :class:`.PatchGraderSubmissionData` or as a dictionary.
        :param submission_id: The id of the submission.

        :returns: Empty response and a 204 status.
        """

        url = "/api/v1/submissions/{submissionId}/grader".format(
            submissionId=submission_id
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

    def get_feedback(
        self: SubmissionService[client.AuthenticatedClient],
        *,
        submission_id: int,
        with_replies: bool = False,
    ) -> t.Union[FeedbackWithReplies, FeedbackWithoutReplies]:
        """Get all feedback for a submission

        :param submission_id: The submission of which you want to get the
            feedback.
        :param with_replies: Do you want to include replies in with your
            comments? Starting with version "O.1" the default value will change
            to `True`.

        :returns: The feedback of this submission.
        """

        url = "/api/v1/submissions/{submissionId}/feedbacks/".format(
            submissionId=submission_id
        )
        params: t.Dict[str, str | int | bool] = {
            "with_replies": with_replies,
        }

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.feedback_with_replies import FeedbackWithReplies
            from ..models.feedback_without_replies import (
                FeedbackWithoutReplies,
            )

            return parsers.JsonResponseParser(
                parsers.make_union(
                    parsers.ParserFor.make(FeedbackWithReplies),
                    parsers.ParserFor.make(FeedbackWithoutReplies),
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

    def get_grade_history(
        self: SubmissionService[client.AuthenticatedClient],
        *,
        submission_id: int,
        page_size: int = 20,
    ) -> paginated.Response[GradeHistory]:
        """Get the grade history for the given submission.

        :param submission_id: The submission for which you want to get the
            grade history.
        :param page_size: The size of a single page, maximum is 50.

        :returns: All the `GradeHistory` objects, which describe the history of
                  this grade.
        """

        url = "/api/v1/submissions/{submissionId}/grade_history/".format(
            submissionId=submission_id
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

        def parse_response(resp: httpx.Response) -> t.Sequence[GradeHistory]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.grade_history import GradeHistory

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(GradeHistory))
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

    def get_root_file_trees(
        self: SubmissionService[client.AuthenticatedClient],
        *,
        submission_id: int,
    ) -> RootFileTreesJSON:
        """Get all the file trees of a submission.

        :param submission_id: The id of the submission of which you want to get
            the file trees.

        :returns: The student and teacher file tree, from the base/root
                  directory of the submission.
        """

        url = "/api/v1/submissions/{submissionId}/root_file_trees/".format(
            submissionId=submission_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.root_file_trees_json import RootFileTreesJSON

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(RootFileTreesJSON)
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

    def get_all_rubric_results(
        self: SubmissionService[client.AuthenticatedClient],
        *,
        submission_id: int,
        page_size: int = 20,
    ) -> paginated.Response[WorkRubricItem]:
        """Get the rubric results of a submission.

        :param submission_id: The id of the submission
        :param page_size: The size of a single page, maximum is 50.

        :returns: The rubric results that are requested.
        """

        url = "/api/v1/submissions/{submissionId}/rubricitems/".format(
            submissionId=submission_id
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

        def parse_response(resp: httpx.Response) -> t.Sequence[WorkRubricItem]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.work_rubric_item import WorkRubricItem

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(WorkRubricItem))
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

    def put_rubric_result(
        self: SubmissionService[client.AuthenticatedClient],
        json_body: PutRubricResultSubmissionData,
        *,
        submission_id: int,
        copy_locked_items: bool = False,
    ) -> PatchRubricResultResponse:
        """Select the given rubric items for the given submission.

        :param json_body: The body of the request. See
            :class:`.PutRubricResultSubmissionData` for information about the
            possible fields. You can provide this data as a
            :class:`.PutRubricResultSubmissionData` or as a dictionary.
        :param submission_id: The submission to unselect the item for.
        :param copy_locked_items: Should we maintain the selected items in
            locked rubric rows.

        :returns: The work of which you updated the rubric items.
        """

        url = "/api/v1/submissions/{submissionId}/rubricitems/".format(
            submissionId=submission_id
        )
        params: t.Dict[str, str | int | bool] = {
            "copy_locked_items": copy_locked_items,
        }

        with self.__client as client:
            resp = client.http.put(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.patch_rubric_result_response import (
                PatchRubricResultResponse,
            )

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(PatchRubricResultResponse)
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
