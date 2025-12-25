"""The endpoints for task_result objects.

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
    from ..models.job import Job
    from ..models.job_history_json import JobHistoryJSON


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class TaskResultService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all(
        self: TaskResultService[client.AuthenticatedClient],
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> JobHistoryJSON:
        """Get all active tasks, all tasks that have not yet been started, a
        page of finished tasks, and the total number of finished tasks.

        :param offset: First finished task to get.
        :param limit: Amount of finished tasks to get.

        :returns: The requested tasks, with the given limits applied to the
                  finished jobs.
        """

        url = "/api/v1/tasks/"
        params: t.Dict[str, str | int | bool] = {
            "offset": offset,
            "limit": limit,
        }

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.job_history_json import JobHistoryJSON

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(JobHistoryJSON)
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
        self: TaskResultService[client.AuthenticatedClient],
        *,
        task_result_id: str,
    ) -> Job:
        """Get the state of a task result.

        To check if the task failed you should use the `state` attribute of the
        returned object as the status code of the response will still be 200.
        It is 200 as we successfully fulfilled the request, which was getting
        the task result.

        :param task_result_id: The task result to get.

        :returns: The retrieved task result.
        """

        url = "/api/v1/task_results/{taskResultId}".format(
            taskResultId=task_result_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
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

    def restart(
        self: TaskResultService[client.AuthenticatedClient],
        *,
        task_result_id: str,
    ) -> None:
        """Restart a task result.

        The restarted task must not be in the `not_started`, `started`, or
        `finished` state.

        :param task_result_id: The task result to restart.

        :returns: Nothing.
        """

        url = "/api/v1/tasks/{taskResultId}/restart".format(
            taskResultId=task_result_id
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

    def revoke(
        self: TaskResultService[client.AuthenticatedClient],
        *,
        task_result_id: str,
    ) -> None:
        """Revoke a task result.

        The revoked task must be in the \"not_started\" state.

        :param task_result_id: The task result to revoke.

        :returns: Nothing.
        """

        url = "/api/v1/tasks/{taskResultId}/revoke".format(
            taskResultId=task_result_id
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
