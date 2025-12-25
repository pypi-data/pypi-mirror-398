"""The endpoints for plagiarism objects.

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
    from ..models.plagiarism_case import PlagiarismCase
    from ..models.plagiarism_match import PlagiarismMatch
    from ..models.plagiarism_run import PlagiarismRun


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class PlagiarismService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get(
        self: PlagiarismService[client.AuthenticatedClient],
        *,
        plagiarism_id: int,
    ) -> PlagiarismRun:
        """Get a `.models.PlagiarismRun`.

        :param plagiarism_id: The of the plagiarism run.

        :returns: An single plagiarism run.
        """

        url = "/api/v1/plagiarism/{plagiarismId}".format(
            plagiarismId=plagiarism_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
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

    def delete(
        self: PlagiarismService[client.AuthenticatedClient],
        *,
        plagiarism_id: int,
    ) -> None:
        """Delete a given plagiarism run and all its cases.

        This is irreversible, so make sure the user really wants this!

        :param plagiarism_id: The id of the run to delete.

        :returns: Nothing.
        """

        url = "/api/v1/plagiarism/{plagiarismId}".format(
            plagiarismId=plagiarism_id
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

    def get_providers(
        self,
        *,
        page_size: int = 20,
    ) -> paginated.Response[t.Mapping[str, t.Any]]:
        """Get all plagiarism providers for this instance.

        :param page_size: The size of a single page, maximum is 50.

        :returns: An array of plagiarism providers.
        """

        url = "/api/v1/plagiarism/"
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
        ) -> t.Sequence[t.Mapping[str, t.Any]]:
            if utils.response_code_matches(resp.status_code, 200):
                return parsers.JsonResponseParser(
                    rqa.List(rqa.LookupMapping(rqa.AnyValue))
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

    def get_case(
        self: PlagiarismService[client.AuthenticatedClient],
        *,
        plagiarism_id: int,
        case_id: int,
    ) -> PlagiarismCase:
        """Get a single plagiarism case.

        :param plagiarism_id: The id of the run the case should belong to.
        :param case_id: The id of the case requested.

        :returns: The requested case.
        """

        url = "/api/v1/plagiarism/{plagiarismId}/cases/{caseId}".format(
            plagiarismId=plagiarism_id, caseId=case_id
        )
        params = None

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.plagiarism_case import PlagiarismCase

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(PlagiarismCase)
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

    def get_log(
        self: PlagiarismService[client.AuthenticatedClient],
        *,
        plagiarism_id: int,
    ) -> bytes:
        """Get the log of a plagiarism run.

        :param plagiarism_id: The id of the run of which you want to get the
            log.

        :returns: The log of the run.
        """

        url = "/api/v1/plagiarism/{plagiarismId}/log".format(
            plagiarismId=plagiarism_id
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

    def get_matches(
        self: PlagiarismService[client.AuthenticatedClient],
        *,
        plagiarism_id: int,
        case_id: int,
        page_size: int = 20,
    ) -> paginated.Response[PlagiarismMatch]:
        """Get the matches in a plagiarism case.

        :param plagiarism_id: The id of the run the case should belong to.
        :param case_id: The id of the case requested.
        :param page_size: The size of a single page, maximum is 50.

        :returns: The matches of this case, ordered by id.
        """

        url = (
            "/api/v1/plagiarism/{plagiarismId}/cases/{caseId}/matches/".format(
                plagiarismId=plagiarism_id, caseId=case_id
            )
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
        ) -> t.Sequence[PlagiarismMatch]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.plagiarism_match import PlagiarismMatch

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(PlagiarismMatch))
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

    def get_cases(
        self: PlagiarismService[client.AuthenticatedClient],
        *,
        plagiarism_id: int,
        q: str = "",
        page_size: int = 20,
    ) -> paginated.Response[PlagiarismCase]:
        """Get all the `.models.PlagiarismCase`s for the given
        `.models.PlagiarismRun`.

        :param plagiarism_id: The of the plagiarism run.
        :param q: Search the cases based on this value.
        :param page_size: The size of a single page, maximum is 50.

        :returns: An array of plagiarism cases.
        """

        url = "/api/v1/plagiarism/{plagiarismId}/cases/".format(
            plagiarismId=plagiarism_id
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

        def parse_response(resp: httpx.Response) -> t.Sequence[PlagiarismCase]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.plagiarism_case import PlagiarismCase

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(PlagiarismCase))
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
