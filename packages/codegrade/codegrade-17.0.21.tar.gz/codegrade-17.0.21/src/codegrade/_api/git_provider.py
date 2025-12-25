"""The endpoints for git_provider objects.

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
    from ..models.connect_repository_git_provider_data import (
        ConnectRepositoryGitProviderData,
    )
    from ..models.create_repository_git_provider_data import (
        CreateRepositoryGitProviderData,
    )
    from ..models.git_repository_like import GitRepositoryLike
    from ..models.job import Job


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class GitProviderService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def connect_repository(
        self: GitProviderService[client.AuthenticatedClient],
        json_body: ConnectRepositoryGitProviderData,
        *,
        provider_id: str,
        token_id: str,
        repository_id: str,
        is_test_student: bool,
        author_id: int,
    ) -> Job:
        """Connect an existing repository to an assignment.

        :param json_body: The body of the request. See
            :class:`.ConnectRepositoryGitProviderData` for information about
            the possible fields. You can provide this data as a
            :class:`.ConnectRepositoryGitProviderData` or as a dictionary.
        :param provider_id: The provider from which you want to connect the
            repo.
        :param token_id: The id of the token used for authentication.
        :param repository_id: The id of the repo to connect.
        :param is_test_student: Is this webhook for the test student?
        :param author_id: The id of the user for which we should get the
            webhook settings.

        :returns: A job that will be started to connect and clone the
                  repository.
        """

        url = "/api/v1/git_providers/{providerId}/tokens/{tokenId}/repositories/{repositoryId}/connect".format(
            providerId=provider_id,
            tokenId=token_id,
            repositoryId=repository_id,
        )
        params: t.Dict[str, str | int | bool] = {
            "is_test_student": is_test_student,
            "author_id": author_id,
        }

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

    def get_all_repositories(
        self: GitProviderService[client.AuthenticatedClient],
        *,
        provider_id: str,
        token_id: str,
        page_size: int = 20,
    ) -> paginated.Response[GitRepositoryLike]:
        """Get all repositories for the given git provider.

        :param provider_id: The provider from which you want to retrieve repos.
        :param token_id: The token to use to retrieve the repos.
        :param page_size: The size of a single page, maximum is 50.

        :returns: The token.
        """

        url = "/api/v1/git_providers/{providerId}/tokens/{tokenId}/repositories/".format(
            providerId=provider_id, tokenId=token_id
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
        ) -> t.Sequence[GitRepositoryLike]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.git_repository_like import GitRepositoryLike

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(GitRepositoryLike))
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

    def create_repository(
        self: GitProviderService[client.AuthenticatedClient],
        json_body: CreateRepositoryGitProviderData,
        *,
        provider_id: str,
        token_id: str,
        is_test_student: bool,
        author_id: int,
    ) -> Job:
        """Create a new repository and connect it to an assignment.

        :param json_body: The body of the request. See
            :class:`.CreateRepositoryGitProviderData` for information about the
            possible fields. You can provide this data as a
            :class:`.CreateRepositoryGitProviderData` or as a dictionary.
        :param provider_id: The provider in which you want to create a new
            repo.
        :param token_id: The id of the token used for authentication.
        :param is_test_student: Is this webhook for the test student?
        :param author_id: The id of the user for which we should get the
            webhook settings.

        :returns: A job that will be started to connect and clone the
                  repository.
        """

        url = "/api/v1/git_providers/{providerId}/tokens/{tokenId}/repositories/".format(
            providerId=provider_id, tokenId=token_id
        )
        params: t.Dict[str, str | int | bool] = {
            "is_test_student": is_test_student,
            "author_id": author_id,
        }

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

    def get_all_templates(
        self: GitProviderService[client.AuthenticatedClient],
        *,
        provider_id: str,
        token_id: str,
        page_size: int = 20,
    ) -> paginated.Response[GitRepositoryLike]:
        """Get all template repositories for the given git provider.

        Note: We do not yet support GitLab templates.

        :param provider_id: The provider from which you want to retrieve repos.
        :param token_id: The token to use to retrieve the repos.
        :param page_size: The size of a single page, maximum is 50.

        :returns: The token.
        """

        url = "/api/v1/git_providers/{providerId}/tokens/{tokenId}/templates/".format(
            providerId=provider_id, tokenId=token_id
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
        ) -> t.Sequence[GitRepositoryLike]:
            if utils.response_code_matches(resp.status_code, 200):
                from ..models.git_repository_like import GitRepositoryLike

                return parsers.JsonResponseParser(
                    rqa.List(parsers.ParserFor.make(GitRepositoryLike))
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
