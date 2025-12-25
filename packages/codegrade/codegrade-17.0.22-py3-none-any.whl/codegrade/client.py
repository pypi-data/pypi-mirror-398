"""The main client used by the CodeGrade API.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

import abc
import datetime
import functools
import getpass
import os
import random
import sys
import time
import typing as t
import uuid
from types import TracebackType

import cg_maybe
import cg_request_args as rqa
import httpx

from .models import (
    CoursePermission as _CoursePermission,
)
from .models import (
    LoginData as _LoginData,
)
from .models import (
    LogoutUserData as _LogoutUserData,
)
from .models import (
    RemovedPermissions as _RemovedPermissions,
)
from .models import (
    SessionRestrictionContext as _SessionRestrictionContext,
)
from .models import (
    SessionRestrictionData as _SessionRestrictionData,
)
from .utils import maybe_input, select_from_paginated_list

_DEFAULT_HOST = os.getenv("CG_HOST", "https://app.codegra.de")

_BaseClientT = t.TypeVar("_BaseClientT", bound="_BaseClient")

if t.TYPE_CHECKING or os.getenv("CG_EAGERIMPORT", False):
    from codegrade._api.about import AboutService as _AboutService
    from codegrade._api.access_plan import (
        AccessPlanService as _AccessPlanService,
    )
    from codegrade._api.assignment import (
        AssignmentService as _AssignmentService,
    )
    from codegrade._api.auto_test import AutoTestService as _AutoTestService
    from codegrade._api.comment import CommentService as _CommentService
    from codegrade._api.course import CourseService as _CourseService
    from codegrade._api.course_price import (
        CoursePriceService as _CoursePriceService,
    )
    from codegrade._api.file import FileService as _FileService
    from codegrade._api.git_provider import (
        GitProviderService as _GitProviderService,
    )
    from codegrade._api.group import GroupService as _GroupService
    from codegrade._api.group_set import GroupSetService as _GroupSetService
    from codegrade._api.login_link import LoginLinkService as _LoginLinkService
    from codegrade._api.lti import LTIService as _LTIService
    from codegrade._api.notification import (
        NotificationService as _NotificationService,
    )
    from codegrade._api.oauth_provider import (
        OAuthProviderService as _OAuthProviderService,
    )
    from codegrade._api.oauth_token import (
        OAuthTokenService as _OAuthTokenService,
    )
    from codegrade._api.permission import (
        PermissionService as _PermissionService,
    )
    from codegrade._api.plagiarism import (
        PlagiarismService as _PlagiarismService,
    )
    from codegrade._api.role import RoleService as _RoleService
    from codegrade._api.saml import SamlService as _SamlService
    from codegrade._api.section import SectionService as _SectionService
    from codegrade._api.site_settings import (
        SiteSettingsService as _SiteSettingsService,
    )
    from codegrade._api.snippet import SnippetService as _SnippetService
    from codegrade._api.sso_provider import (
        SSOProviderService as _SSOProviderService,
    )
    from codegrade._api.submission import (
        SubmissionService as _SubmissionService,
    )
    from codegrade._api.task_result import (
        TaskResultService as _TaskResultService,
    )
    from codegrade._api.tenant import TenantService as _TenantService
    from codegrade._api.transaction import (
        TransactionService as _TransactionService,
    )
    from codegrade._api.user import UserService as _UserService
    from codegrade._api.user_setting import (
        UserSettingService as _UserSettingService,
    )
    from codegrade._api.webhook import WebhookService as _WebhookService


class RetryingTransport(httpx.BaseTransport):
    """An httpx transport that adds automatic retries with exponential backoff.
    It wraps another transport to handle the actual sending of requests.
    """

    def __init__(
        self,
        # Transport that actually performs the request.
        transport: httpx.BaseTransport,
        *,
        # Maximum _total_ number of attempts per request, _including the first_.
        # Minimum is 1 (no retry). Example: `max_tries=2` means at most 1 retry.
        max_tries: int = 4,
        # Upper bound for the sleep between any two attempts. If the computed
        # backoff (with jitter) exceeds this, the delay is truncated to this cap.
        # Rate limit delays that exceed it, will _not_ be capped.
        max_delay_between_attempts: datetime.timedelta = datetime.timedelta(
            seconds=30
        ),
        # Seconds base for the backoff calculation.
        backoff_initial: float = 0.5,
        # The exponential multiplier per failed attempt, backoff_factor ** n.
        backoff_factor: float = 2.0,
        # Fraction of the base delay to add as random jitter, 0 - 20%.
        jitter_factor: float = 0.2,
    ) -> None:
        self._transport = transport
        self._max_tries = max(1, int(max_tries))
        self._max_delay_between_attempts = float(
            max_delay_between_attempts.total_seconds()
        )
        self._backoff_initial = float(backoff_initial)
        self._backoff_factor = float(backoff_factor)
        self._jitter_factor = float(jitter_factor)

    def __enter__(self) -> "RetryingTransport":
        self._transport.__enter__()
        return self

    def __exit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]] = None,
        exc_value: t.Optional[BaseException] = None,
        traceback: t.Optional[TracebackType] = None,
    ) -> None:
        self._transport.__exit__(exc_type, exc_value, traceback)

    def close(self) -> None:
        if self._transport is not None:
            self._transport.close()

    def _is_retryable_method(self, method: str) -> bool:
        return method.upper() in {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}

    def _should_retry_request(
        self,
        failed_attempt: int,
        request: httpx.Request,
    ) -> bool:
        return failed_attempt < self._max_tries and self._is_retryable_method(
            request.method
        )

    def _should_retry_response(
        self,
        failed_attempt: int,
        request: httpx.Request,
        response: httpx.Response,
    ) -> bool:
        is_retryable_request = self._should_retry_request(
            failed_attempt, request
        )

        if not is_retryable_request:
            return False

        is_retryable_status = (
            response.status_code == 429 or 500 <= response.status_code <= 599
        )

        return is_retryable_status

    def _get_backoff_delay(self, failed_attempt: int) -> datetime.timedelta:
        base = self._backoff_initial * (
            self._backoff_factor ** (failed_attempt - 1)
        )
        jitter = self._jitter_factor * base * random.random()
        seconds = min(self._max_delay_between_attempts, base + jitter)
        return datetime.timedelta(seconds=seconds)

    def _get_delay_from_response(
        self, response: httpx.Response
    ) -> cg_maybe.Maybe[datetime.timedelta]:
        from .models import RateLimitExceededException

        # Pattern used from httpx.Client::send, before returning response.
        # We must be able to get the json body from the response in order
        # to parse the RateLimitException from it, and get the delay to wait.
        try:
            response.read()
        except BaseException as exc:
            response.close()
            raise exc

        try:
            rateLimitException = RateLimitExceededException.from_dict(
                response.json(), response=response
            )
            return cg_maybe.of(rateLimitException.retry_after)
        except (rqa.ParseError, ValueError):
            return cg_maybe.Nothing

    def _get_delay_between_attempts(
        self,
        failed_attempt: int,
        *,
        response: httpx.Response | None,
    ) -> datetime.timedelta:
        delay = self._get_backoff_delay(failed_attempt)

        if response is not None:
            return self._get_delay_from_response(response).or_default(delay)

        return delay

    def _sleep(
        self,
        failed_attempt: int,
        *,
        response: httpx.Response | None,
    ) -> None:
        time.sleep(
            self._get_delay_between_attempts(
                failed_attempt, response=response
            ).total_seconds()
        )

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        attempt = 0
        while True:
            attempt += 1
            try:
                response = self._transport.handle_request(request)
            except httpx.HTTPError:
                if self._should_retry_request(attempt, request):
                    self._sleep(attempt, response=None)
                    continue
                raise

            if self._should_retry_response(attempt, request, response):
                self._sleep(attempt, response=response)
                continue

            return response


class _BaseClient:
    """A base class for keeping track of data related to the API."""

    def __init__(self: "_BaseClientT", base_url: str) -> None:
        # Open level makes it possible to efficiently nest the context manager.
        self.__open_level = 0
        self.base_url = base_url

        self.__http: t.Optional[httpx.Client] = None

    def _get_headers(self) -> t.Mapping[str, str]:
        """Get headers to be used in all endpoints"""
        return {}

    @abc.abstractmethod
    def _make_http(self) -> httpx.Client:
        raise NotImplementedError

    @property
    def http(self) -> httpx.Client:
        if self.__http is None:
            self.__http = self._make_http()
        return self.__http

    def __enter__(self: _BaseClientT) -> _BaseClientT:
        if self.__open_level == 0:
            self.http.__enter__()
        self.__open_level += 1
        return self

    def __exit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]] = None,
        exc_value: t.Optional[BaseException] = None,
        traceback: t.Optional[TracebackType] = None,
    ) -> None:
        self.__open_level -= 1
        if self.__open_level == 0:
            self.http.__exit__(exc_type, exc_value, traceback)
            self.__http = None

    @functools.cached_property
    def about(self: _BaseClientT) -> "_AboutService[_BaseClientT]":
        """Get a :class:`.AboutService` to do requests concerning About."""
        import codegrade._api.about as m

        return m.AboutService(self)

    @functools.cached_property
    def access_plan(self: _BaseClientT) -> "_AccessPlanService[_BaseClientT]":
        """Get a :class:`.AccessPlanService` to do requests concerning
        AccessPlan.
        """
        import codegrade._api.access_plan as m

        return m.AccessPlanService(self)

    @functools.cached_property
    def assignment(self: _BaseClientT) -> "_AssignmentService[_BaseClientT]":
        """Get a :class:`.AssignmentService` to do requests concerning
        Assignment.
        """
        import codegrade._api.assignment as m

        return m.AssignmentService(self)

    @functools.cached_property
    def auto_test(self: _BaseClientT) -> "_AutoTestService[_BaseClientT]":
        """Get a :class:`.AutoTestService` to do requests concerning AutoTest."""
        import codegrade._api.auto_test as m

        return m.AutoTestService(self)

    @functools.cached_property
    def comment(self: _BaseClientT) -> "_CommentService[_BaseClientT]":
        """Get a :class:`.CommentService` to do requests concerning Comment."""
        import codegrade._api.comment as m

        return m.CommentService(self)

    @functools.cached_property
    def course(self: _BaseClientT) -> "_CourseService[_BaseClientT]":
        """Get a :class:`.CourseService` to do requests concerning Course."""
        import codegrade._api.course as m

        return m.CourseService(self)

    @functools.cached_property
    def course_price(
        self: _BaseClientT,
    ) -> "_CoursePriceService[_BaseClientT]":
        """Get a :class:`.CoursePriceService` to do requests concerning
        CoursePrice.
        """
        import codegrade._api.course_price as m

        return m.CoursePriceService(self)

    @functools.cached_property
    def file(self: _BaseClientT) -> "_FileService[_BaseClientT]":
        """Get a :class:`.FileService` to do requests concerning File."""
        import codegrade._api.file as m

        return m.FileService(self)

    @functools.cached_property
    def git_provider(
        self: _BaseClientT,
    ) -> "_GitProviderService[_BaseClientT]":
        """Get a :class:`.GitProviderService` to do requests concerning
        GitProvider.
        """
        import codegrade._api.git_provider as m

        return m.GitProviderService(self)

    @functools.cached_property
    def group(self: _BaseClientT) -> "_GroupService[_BaseClientT]":
        """Get a :class:`.GroupService` to do requests concerning Group."""
        import codegrade._api.group as m

        return m.GroupService(self)

    @functools.cached_property
    def group_set(self: _BaseClientT) -> "_GroupSetService[_BaseClientT]":
        """Get a :class:`.GroupSetService` to do requests concerning GroupSet."""
        import codegrade._api.group_set as m

        return m.GroupSetService(self)

    @functools.cached_property
    def login_link(self: _BaseClientT) -> "_LoginLinkService[_BaseClientT]":
        """Get a :class:`.LoginLinkService` to do requests concerning
        LoginLink.
        """
        import codegrade._api.login_link as m

        return m.LoginLinkService(self)

    @functools.cached_property
    def lti(self: _BaseClientT) -> "_LTIService[_BaseClientT]":
        """Get a :class:`.LTIService` to do requests concerning LTI."""
        import codegrade._api.lti as m

        return m.LTIService(self)

    @functools.cached_property
    def notification(
        self: _BaseClientT,
    ) -> "_NotificationService[_BaseClientT]":
        """Get a :class:`.NotificationService` to do requests concerning
        Notification.
        """
        import codegrade._api.notification as m

        return m.NotificationService(self)

    @functools.cached_property
    def oauth_provider(
        self: _BaseClientT,
    ) -> "_OAuthProviderService[_BaseClientT]":
        """Get a :class:`.OAuthProviderService` to do requests concerning
        OAuthProvider.
        """
        import codegrade._api.oauth_provider as m

        return m.OAuthProviderService(self)

    @functools.cached_property
    def oauth_token(self: _BaseClientT) -> "_OAuthTokenService[_BaseClientT]":
        """Get a :class:`.OAuthTokenService` to do requests concerning
        OAuthToken.
        """
        import codegrade._api.oauth_token as m

        return m.OAuthTokenService(self)

    @functools.cached_property
    def permission(self: _BaseClientT) -> "_PermissionService[_BaseClientT]":
        """Get a :class:`.PermissionService` to do requests concerning
        Permission.
        """
        import codegrade._api.permission as m

        return m.PermissionService(self)

    @functools.cached_property
    def plagiarism(self: _BaseClientT) -> "_PlagiarismService[_BaseClientT]":
        """Get a :class:`.PlagiarismService` to do requests concerning
        Plagiarism.
        """
        import codegrade._api.plagiarism as m

        return m.PlagiarismService(self)

    @functools.cached_property
    def role(self: _BaseClientT) -> "_RoleService[_BaseClientT]":
        """Get a :class:`.RoleService` to do requests concerning Role."""
        import codegrade._api.role as m

        return m.RoleService(self)

    @functools.cached_property
    def saml(self: _BaseClientT) -> "_SamlService[_BaseClientT]":
        """Get a :class:`.SamlService` to do requests concerning Saml."""
        import codegrade._api.saml as m

        return m.SamlService(self)

    @functools.cached_property
    def section(self: _BaseClientT) -> "_SectionService[_BaseClientT]":
        """Get a :class:`.SectionService` to do requests concerning Section."""
        import codegrade._api.section as m

        return m.SectionService(self)

    @functools.cached_property
    def site_settings(
        self: _BaseClientT,
    ) -> "_SiteSettingsService[_BaseClientT]":
        """Get a :class:`.SiteSettingsService` to do requests concerning
        SiteSettings.
        """
        import codegrade._api.site_settings as m

        return m.SiteSettingsService(self)

    @functools.cached_property
    def snippet(self: _BaseClientT) -> "_SnippetService[_BaseClientT]":
        """Get a :class:`.SnippetService` to do requests concerning Snippet."""
        import codegrade._api.snippet as m

        return m.SnippetService(self)

    @functools.cached_property
    def sso_provider(
        self: _BaseClientT,
    ) -> "_SSOProviderService[_BaseClientT]":
        """Get a :class:`.SSOProviderService` to do requests concerning
        SSOProvider.
        """
        import codegrade._api.sso_provider as m

        return m.SSOProviderService(self)

    @functools.cached_property
    def submission(self: _BaseClientT) -> "_SubmissionService[_BaseClientT]":
        """Get a :class:`.SubmissionService` to do requests concerning
        Submission.
        """
        import codegrade._api.submission as m

        return m.SubmissionService(self)

    @functools.cached_property
    def task_result(self: _BaseClientT) -> "_TaskResultService[_BaseClientT]":
        """Get a :class:`.TaskResultService` to do requests concerning
        TaskResult.
        """
        import codegrade._api.task_result as m

        return m.TaskResultService(self)

    @functools.cached_property
    def tenant(self: _BaseClientT) -> "_TenantService[_BaseClientT]":
        """Get a :class:`.TenantService` to do requests concerning Tenant."""
        import codegrade._api.tenant as m

        return m.TenantService(self)

    @functools.cached_property
    def transaction(self: _BaseClientT) -> "_TransactionService[_BaseClientT]":
        """Get a :class:`.TransactionService` to do requests concerning
        Transaction.
        """
        import codegrade._api.transaction as m

        return m.TransactionService(self)

    @functools.cached_property
    def user(self: _BaseClientT) -> "_UserService[_BaseClientT]":
        """Get a :class:`.UserService` to do requests concerning User."""
        import codegrade._api.user as m

        return m.UserService(self)

    @functools.cached_property
    def user_setting(
        self: _BaseClientT,
    ) -> "_UserSettingService[_BaseClientT]":
        """Get a :class:`.UserSettingService` to do requests concerning
        UserSetting.
        """
        import codegrade._api.user_setting as m

        return m.UserSettingService(self)

    @functools.cached_property
    def webhook(self: _BaseClientT) -> "_WebhookService[_BaseClientT]":
        """Get a :class:`.WebhookService` to do requests concerning Webhook."""
        import codegrade._api.webhook as m

        return m.WebhookService(self)


class Client(_BaseClient):
    """A class used to do unauthenticated requests to CodeGrade"""

    __slots__ = ()

    def _make_http(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            headers={
                "User-Agent": "CodeGradeAPI/17.0.22",
            },
            follow_redirects=True,
            transport=RetryingTransport(httpx.HTTPTransport()),
        )


class AuthenticatedClient(_BaseClient):
    """A Client which has been authenticated for use on secured endpoints"""

    __slots__ = ("token",)

    def __init__(self, base_url: str, token: str):
        super().__init__(base_url)
        self.token = token

    def _make_http(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "CodeGradeAPI/17.0.22",
            },
            follow_redirects=True,
            transport=RetryingTransport(httpx.HTTPTransport()),
        )

    @staticmethod
    def _prepare_host(host: str) -> str:
        if not host.startswith("http"):
            return "https://{}".format(host)
        elif host.startswith("http://"):
            raise ValueError("Non https:// schemes are not supported")
        else:
            return host

    @classmethod
    def get(
        cls,
        username: str,
        password: str,
        tenant: t.Optional[str] = None,
        host: str = _DEFAULT_HOST,
    ) -> "AuthenticatedClient":
        """Get an :class:`.AuthenticatedClient` by logging in with your
        username and password.

        .. code-block:: python

            with AuthenticatedClient.get(
                username='my-username',
                password=os.getenv('CG_PASS'),
                tenant='My University',
            ) as client:
                print('Hi I am {}'.format(client.user.get().name)

        :param username: Your CodeGrade username.
        :param password: Your CodeGrade password, if you do not know your
            password you can set it by following `these steps.
            <https://help.codegrade.com/faq/setting-up-a-password-for-my-account>`_
        :param tenant: The id or name of your tenant in CodeGrade. This is the
            name you click on the login screen.
        :param host: The CodeGrade instance you want to use.

        :returns: A client that you can use to do authenticated requests to
                  CodeGrade. We advise you to use it in combination with a
                  ``with`` block (i.e. as a contextmanager) for the highest
                  efficiency.
        """
        host = cls._prepare_host(host)

        with Client(host) as client:
            try:
                tenant_id = str(uuid.UUID(tenant))
            except ValueError:
                # Given tenant is not an id, find it by name
                all_tenants = list(
                    client.tenant.get_all(page_size=100, q=tenant or "")
                )
                if tenant is None:
                    if len(all_tenants) == 1:
                        tenant_id = all_tenants[0].id
                    else:
                        raise ValueError(
                            "No tenant specified and found more than 1 tenant on the instance. Found tenants are: {}".format(
                                ", ".join(t.name for t in all_tenants),
                            )
                        )
                else:
                    tenants = {t.name: t for t in all_tenants}
                    if tenant not in tenants:
                        raise KeyError(
                            'Could not find tenant "{}", known tenants are: {}'.format(
                                tenant,
                                ", ".join(t.name for t in all_tenants),
                            )
                        )
                    tenant_id = tenants[tenant].id

            res = client.user.login(
                json_body=_LoginData(
                    username=username,
                    password=password,
                    tenant_id=tenant_id,
                )
            )

        return cls.get_with_token(
            token=res.access_token,
            host=host,
            check=False,
        )

    @classmethod
    def get_with_token(
        cls,
        token: str,
        host: str = _DEFAULT_HOST,
        *,
        check: bool = True,
    ) -> "AuthenticatedClient":
        """Get an :class:`.AuthenticatedClient` by logging with an access
        token.

        :param token: The access token you want to use to login.
        :param host: The CodeGrade instance you want to login to.
        :param check: If ``False`` we won't check if your token actually works.

        :returns: A new ``AuthenticatedClient``.
        """
        host = cls._prepare_host(host)

        res = cls(host, token)
        if check:
            try:
                res.user.get()
            except BaseException as exc:
                raise ValueError(
                    "Failed to retrieve connected user, make sure your token has not expired"
                ) from exc
        return res

    @classmethod
    def get_from_cli(cls) -> "AuthenticatedClient":
        """Get an :class:`.AuthenticatedClient` by logging in through command
        line interface.

        :returns: A new ``AuthenticatedClient``.
        """
        host = (
            maybe_input("Your instance", _DEFAULT_HOST)
            .map(cls._prepare_host)
            .try_extract(sys.exit)
        )
        with Client(host) as client:
            tenant = select_from_paginated_list(
                "Select your tenant",
                client.tenant.get_all(page_size=100),
                lambda t: t.name,
            ).try_extract(sys.exit)
        username = maybe_input("Your username").try_extract(sys.exit)
        password = getpass.getpass("Your password: ")
        if not password:
            sys.exit()

        return cls.get(
            username=username, password=password, host=host, tenant=tenant.id
        )

    def restrict(
        client,
        *,
        course_id: t.Optional[int] = None,
        removed_permissions: t.Sequence[_CoursePermission] = (),
    ) -> None:
        """Restrict this authenticated client to a specific course and/or
        reduced permissions.

        :param course_id: If provided, restrict access to only this course.
        :param removed_permissions: If provided, remove specific permissions in
            the current session.
        """
        restriction = _SessionRestrictionData(
            for_context=cg_maybe.from_nullable(course_id).map(
                lambda cid: _SessionRestrictionContext(cid),
            ),
            removed_permissions=(
                cg_maybe.of(_RemovedPermissions(removed_permissions))
                if removed_permissions
                else cg_maybe.Nothing
            ),
        )

        restricted_login = client.user.restrict(restriction)
        client.user.logout(_LogoutUserData(token=client.token))
        client.token = restricted_login.access_token
        client.http.headers["Authorization"] = f"Bearer {client.token}"

    @classmethod
    def get_from_cli_for_course(
        cls, course_id: t.Optional[int] = None
    ) -> "AuthenticatedClient":
        """Get an :class:`.AuthenticatedClient` by logging in through command
        line interface for a specific course.

        :param course_id: The optional ID of the course you want to log into.

        :returns: A new ``AuthenticatedClient``.
        """
        client = cls.get_from_cli()

        if course_id is not None:
            client.restrict(course_id=course_id, removed_permissions=[])
            return client

        course = select_from_paginated_list(
            "Select your course",
            client.course.get_all(page_size=20),
            lambda c: c.name,
        ).try_extract(sys.exit)

        client.restrict(course_id=course.id, removed_permissions=[])
        return client
