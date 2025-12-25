"""The endpoints for auto_test objects.

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
    from ..models.all_auto_test_results import AllAutoTestResults
    from ..models.auto_test import AutoTest
    from ..models.auto_test_result import AutoTestResult
    from ..models.auto_test_set import AutoTestSet
    from ..models.auto_test_suite import AutoTestSuite
    from ..models.copy_auto_test_data import CopyAutoTestData
    from ..models.create_auto_test_data import CreateAutoTestData
    from ..models.create_output_html_proxy_auto_test_data import (
        CreateOutputHtmlProxyAutoTestData,
    )
    from ..models.extended_auto_test_result import ExtendedAutoTestResult
    from ..models.extended_auto_test_run import ExtendedAutoTestRun
    from ..models.patch_auto_test_data import PatchAutoTestData
    from ..models.proxy import Proxy
    from ..models.update_set_auto_test_data import UpdateSetAutoTestData
    from ..models.update_suite_auto_test_data import UpdateSuiteAutoTestData


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class AutoTestService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def copy(
        self: AutoTestService[client.AuthenticatedClient],
        json_body: CopyAutoTestData,
        *,
        auto_test_id: int,
    ) -> AutoTest:
        """Copy the given `AutoTest` configuration.

        :param json_body: The body of the request. See
            :class:`.CopyAutoTestData` for information about the possible
            fields. You can provide this data as a :class:`.CopyAutoTestData`
            or as a dictionary.
        :param auto_test_id: The id of the `AutoTest` config which should be
            copied.

        :returns: The copied `AutoTest` configuration.
        """

        url = "/api/v1/auto_tests/{autoTestId}/copy".format(
            autoTestId=auto_test_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
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

    def create(
        self: AutoTestService[client.AuthenticatedClient],
        multipart_data: CreateAutoTestData,
    ) -> AutoTest:
        """Create a new `AutoTest` configuration.

        :param multipart_data: The data that should form the body of the
            request. See :class:`.CreateAutoTestData` for information about the
            possible fields.

        :returns: The newly created `AutoTest`.
        """

        url = "/api/v1/auto_tests/"
        params = None

        data, files = utils.to_multipart(utils.to_dict(multipart_data))

        with self.__client as client:
            resp = client.http.post(
                url=url, files=files, data=data, params=params
            )
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

    def add_set(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
    ) -> AutoTestSet:
        """Create a new set within an `AutoTest`

        :param auto_test_id: The id of the `AutoTest` wherein you want to
            create a set.

        :returns: The newly created set.
        """

        url = "/api/v1/auto_tests/{autoTestId}/sets/".format(
            autoTestId=auto_test_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.auto_test_set import AutoTestSet

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(AutoTestSet)
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
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
    ) -> AutoTest:
        """Get the extended version of an `AutoTest` and its runs.

        :param auto_test_id: The id of the `AutoTest` to get.

        :returns: The extended serialization of an `AutoTest` and the extended
                  serialization of its runs.
        """

        url = "/api/v1/auto_tests/{autoTestId}".format(autoTestId=auto_test_id)
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

    def delete(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
    ) -> None:
        """Delete the given `AutoTest`.

        This route fails if the `AutoTest` has any runs, which should be
        deleted separately.

        :param auto_test_id: The `AutoTest` that should be deleted.

        :returns: Nothing.
        """

        url = "/api/v1/auto_tests/{autoTestId}".format(autoTestId=auto_test_id)
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
        self: AutoTestService[client.AuthenticatedClient],
        multipart_data: PatchAutoTestData,
        *,
        auto_test_id: int,
    ) -> AutoTest:
        """Update the settings of an `AutoTest` configuration.

        :param multipart_data: The data that should form the body of the
            request. See :class:`.PatchAutoTestData` for information about the
            possible fields.
        :param auto_test_id: The id of the `AutoTest` you want to update.

        :returns: The updated `AutoTest`.
        """

        url = "/api/v1/auto_tests/{autoTestId}".format(autoTestId=auto_test_id)
        params = None

        data, files = utils.to_multipart(utils.to_dict(multipart_data))

        with self.__client as client:
            resp = client.http.patch(
                url=url, files=files, data=data, params=params
            )
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

    def get_run(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
        run_id: int,
    ) -> ExtendedAutoTestRun:
        """Get the extended version of an `AutoTestRun`.

        :param auto_test_id: The id of the `AutoTest` which is connected to the
            requested run.
        :param run_id: The id of the run to get.

        :returns: The extended version of an `AutoTestRun`.
        """

        url = "/api/v1/auto_tests/{autoTestId}/runs/{runId}".format(
            autoTestId=auto_test_id, runId=run_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_auto_test_run import ExtendedAutoTestRun

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedAutoTestRun)
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

    def stop_run(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
        run_id: int,
    ) -> None:
        """Delete an `AutoTest` run, this makes it possible to edit the
        `AutoTest`.

        This also clears the rubric categories filled in by the `AutoTest`.

        :param auto_test_id: The id of the `AutoTest` of which the run should
            be deleted.
        :param run_id: The id of the run which should be deleted.

        :returns: Nothing.
        """

        url = "/api/v1/auto_tests/{autoTestId}/runs/{runId}".format(
            autoTestId=auto_test_id, runId=run_id
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

    def delete_set(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
        auto_test_set_id: int,
    ) -> None:
        """Delete an `AutoTestSet` (also known as level).

        :param auto_test_id: The id of the `AutoTest` of the to be deleted set.
        :param auto_test_set_id: The id of the `AutoTestSet` that should be
            deleted.

        :returns: Nothing.
        """

        url = "/api/v1/auto_tests/{autoTestId}/sets/{autoTestSetId}".format(
            autoTestId=auto_test_id, autoTestSetId=auto_test_set_id
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

    def update_set(
        self: AutoTestService[client.AuthenticatedClient],
        json_body: UpdateSetAutoTestData,
        *,
        auto_test_id: int,
        auto_test_set_id: int,
    ) -> AutoTestSet:
        """Update the given `AutoTestSet` (also known as level).

        :param json_body: The body of the request. See
            :class:`.UpdateSetAutoTestData` for information about the possible
            fields. You can provide this data as a
            :class:`.UpdateSetAutoTestData` or as a dictionary.
        :param auto_test_id: The id of the `AutoTest` of the set that should be
            updated.
        :param auto_test_set_id: The id of the `AutoTestSet` that should be
            updated.

        :returns: The updated set.
        """

        url = "/api/v1/auto_tests/{autoTestId}/sets/{autoTestSetId}".format(
            autoTestId=auto_test_id, autoTestSetId=auto_test_set_id
        )
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.auto_test_set import AutoTestSet

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(AutoTestSet)
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

    def delete_suite(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        test_id: int,
        set_id: int,
        suite_id: int,
    ) -> None:
        """Delete an `AutoTestSuite` (also known as category).

        :param test_id: The id of the `AutoTest` where the suite is located in.
        :param set_id: The id of the `AutoTestSet` where the suite is located
            in.
        :param suite_id: The id of the `AutoTestSuite` you want to delete.

        :returns: Nothing.
        """

        url = (
            "/api/v1/auto_tests/{testId}/sets/{setId}/suites/{suiteId}".format(
                testId=test_id, setId=set_id, suiteId=suite_id
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

    def get_result(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
        run_id: int,
        result_id: int,
    ) -> ExtendedAutoTestResult:
        """Get the extended version of an `AutoTest` result.

        :param auto_test_id: The id of the `AutoTest` in which the result is
            located.
        :param run_id: The id of run in which the result is located.
        :param result_id: The id of the result you want to get.

        :returns: The extended version of a `AutoTestResult`.
        """

        url = "/api/v1/auto_tests/{autoTestId}/runs/{runId}/results/{resultId}".format(
            autoTestId=auto_test_id, runId=run_id, resultId=result_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_auto_test_result import (
                ExtendedAutoTestResult,
            )

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedAutoTestResult)
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

    def create_output_html_proxy(
        self: AutoTestService[client.AuthenticatedClient],
        json_body: CreateOutputHtmlProxyAutoTestData,
        *,
        auto_test_id: int,
        run_id: int,
        result_id: int,
        suite_id: int,
    ) -> Proxy:
        """Create a proxy to view the files of the given AT result through.

        This allows you to view files of an AutoTest result (within a suite)
        without authentication for a limited time.

        :param json_body: The body of the request. See
            :class:`.CreateOutputHtmlProxyAutoTestData` for information about
            the possible fields. You can provide this data as a
            :class:`.CreateOutputHtmlProxyAutoTestData` or as a dictionary.
        :param auto_test_id: The id of the AutoTest in which the result is
            located.
        :param run_id: The id of run in which the result is located.
        :param result_id: The id of the result from which you want to get the
            files.
        :param suite_id: The suite from which you want to proxy the output
            files.

        :returns: The created proxy.
        """

        url = "/api/v1/auto_tests/{autoTestId}/runs/{runId}/results/{resultId}/suites/{suiteId}/proxy".format(
            autoTestId=auto_test_id,
            runId=run_id,
            resultId=result_id,
            suiteId=suite_id,
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

    def get_result_by_submission(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
        run_id: int,
        submission_id: int,
    ) -> ExtendedAutoTestResult:
        """Get the `AutoTest` result for a submission.

        :param auto_test_id: The id of the `AutoTest` in which to get the
            result.
        :param run_id: The id of the `AutoTestRun` in which to get the result.
        :param submission_id: The id of the submission from which you want to
            get the result.

        :returns: The `AutoTest` result for the given data.
        """

        url = "/api/v1/auto_tests/{autoTestId}/runs/{runId}/submissions/{submissionId}/result".format(
            autoTestId=auto_test_id, runId=run_id, submissionId=submission_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_auto_test_result import (
                ExtendedAutoTestResult,
            )

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedAutoTestResult)
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

    def get_results_by_user(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
        run_id: int,
        user_id: int,
    ) -> t.Sequence[AutoTestResult]:
        """Get all `AutoTest` results for a given user.

        If you don't have permission to see the results of the requested user
        an empty list will be returned.

        :param auto_test_id: The id of the `AutoTest` in which to get the
            results.
        :param run_id: The id of the `AutoTestRun` in which to get the results.
        :param user_id: The id of the user of which we should get the results.

        :returns: The list of `AutoTest` results for the given user, sorted
                  from oldest to latest.
        """

        url = "/api/v1/auto_tests/{autoTestId}/runs/{runId}/users/{userId}/results/".format(
            autoTestId=auto_test_id, runId=run_id, userId=user_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.auto_test_result import AutoTestResult

            return parsers.JsonResponseParser(
                rqa.List(parsers.ParserFor.make(AutoTestResult))
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

    def get_attachment(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
        run_id: int,
        step_result_id: int,
    ) -> bytes:
        """Get the attachment of an `AutoTest` step.

        :param auto_test_id: The id of the `AutoTest` in which the result is
            located.
        :param run_id: The id of run in which the result is located.
        :param step_result_id: The id of the step result of which you want the
            attachment.

        :returns: The attachment data, as an application/octet-stream.
        """

        url = "/api/v1/auto_tests/{autoTestId}/runs/{runId}/step_results/{stepResultId}/attachment".format(
            autoTestId=auto_test_id, runId=run_id, stepResultId=step_result_id
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

    def get_fixture(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
        fixture_id: int,
    ) -> bytes:
        """Get the contents of the given `AutoTestFixture`.

        :param auto_test_id: The `AutoTest` this fixture is linked to.
        :param fixture_id: The id of the fixture which you want the content.

        :returns: The content of the given fixture.
        """

        url = "/api/v1/auto_tests/{autoTestId}/fixtures/{fixtureId}".format(
            autoTestId=auto_test_id, fixtureId=fixture_id
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

    def get_not_started_results(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        offset: int = 0,
        limit: int = 50,
        state: t.Literal["not_started"] = "not_started",
    ) -> AllAutoTestResults:
        """Get all `AutoTest` results on this instance.

        :param offset: First non started result to get.
        :param limit: Amount of non started results to get.
        :param state: The state the results should be in, currently only
            `not_started` is supported.

        :returns: The (limited) results of this instance, and the total amount
                  of non requested results.
        """

        url = "/api/v1/auto_test_results/"
        params: t.Dict[str, str | int | bool] = {
            "offset": offset,
            "limit": limit,
            "state": state,
        }

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.all_auto_test_results import AllAutoTestResults

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(AllAutoTestResults)
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

    def hide_fixture(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
        fixture_id: int,
    ) -> None:
        """Change the visibility of the given fixture.

        Doing a `POST` request to this route will hide the fixture, doing a
        `DELETE` request to this route will set `hidden` to `False`.

        :param auto_test_id: The `AutoTest` this fixture is linked to.
        :param fixture_id: The fixture which you to hide or show.

        :returns: Nothing.
        """

        url = (
            "/api/v1/auto_tests/{autoTestId}/fixtures/{fixtureId}/hide".format(
                autoTestId=auto_test_id, fixtureId=fixture_id
            )
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

    def show_fixture(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
        fixture_id: int,
    ) -> None:
        """Change the visibility of the given fixture.

        Doing a `POST` request to this route will hide the fixture, doing a
        `DELETE` request to this route will set `hidden` to `False`.

        :param auto_test_id: The `AutoTest` this fixture is linked to.
        :param fixture_id: The fixture which you to hide or show.

        :returns: Nothing.
        """

        url = (
            "/api/v1/auto_tests/{autoTestId}/fixtures/{fixtureId}/hide".format(
                autoTestId=auto_test_id, fixtureId=fixture_id
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

    def restart_result(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
        run_id: int,
        result_id: int,
    ) -> ExtendedAutoTestResult:
        """Restart an `AutoTest` result.

        :param auto_test_id: The id of the `AutoTest` in which the result is
            located.
        :param run_id: The id of run in which the result is located.
        :param result_id: The id of the result you want to restart.

        :returns: The extended version of a `AutoTestResult`.
        """

        url = "/api/v1/auto_tests/{autoTestId}/runs/{runId}/results/{resultId}/restart".format(
            autoTestId=auto_test_id, runId=run_id, resultId=result_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_auto_test_result import (
                ExtendedAutoTestResult,
            )

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedAutoTestResult)
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

    def start_run(
        self: AutoTestService[client.AuthenticatedClient],
        *,
        auto_test_id: int,
    ) -> ExtendedAutoTestRun:
        """Start a run for the given `AutoTest`.

        :param auto_test_id: The id of the `AutoTest` for which you want to
            start a run.

        :returns: The started run or a empty mapping if you do not have
                  permission to see `AutoTest` runs.
        """

        url = "/api/v1/auto_tests/{autoTestId}/runs/".format(
            autoTestId=auto_test_id
        )
        params = None

        with self.__client as client:
            resp = client.http.post(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.extended_auto_test_run import ExtendedAutoTestRun

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(ExtendedAutoTestRun)
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

    def update_suite(
        self: AutoTestService[client.AuthenticatedClient],
        json_body: UpdateSuiteAutoTestData,
        *,
        auto_test_id: int,
        set_id: int,
    ) -> AutoTestSuite:
        """Update or create a `AutoTestSuite` (also known as category)

        :param json_body: The body of the request. See
            :class:`.UpdateSuiteAutoTestData` for information about the
            possible fields. You can provide this data as a
            :class:`.UpdateSuiteAutoTestData` or as a dictionary.
        :param auto_test_id: The id of the `AutoTest` in which this suite
            should be created.
        :param set_id: The id the `AutoTestSet` in which this suite should be
            created.

        :returns: The just updated or created `AutoTestSuite`.
        """

        url = "/api/v1/auto_tests/{autoTestId}/sets/{setId}/suites/".format(
            autoTestId=auto_test_id, setId=set_id
        )
        params = None

        with self.__client as client:
            resp = client.http.patch(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.auto_test_suite import AutoTestSuite

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(AutoTestSuite)
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
