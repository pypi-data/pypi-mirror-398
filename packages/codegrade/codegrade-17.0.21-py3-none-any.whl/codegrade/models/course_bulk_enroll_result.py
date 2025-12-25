"""The module that defines the ``CourseBulkEnrollResult`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .user import User, UserParser
from .user_info_with_role import UserInfoWithRole


@dataclass
class CourseBulkEnrollResult:
    """Processed users in a bulk enroll request."""

    #: List of users that have been enrolled in the course.
    enrolled_users: t.Sequence[User]
    #: List of users not created because of incompatibility with SSO.
    sso_incompatible_users: t.Sequence[UserInfoWithRole]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "enrolled_users",
                rqa.List(UserParser),
                doc="List of users that have been enrolled in the course.",
            ),
            rqa.RequiredArgument(
                "sso_incompatible_users",
                rqa.List(parsers.ParserFor.make(UserInfoWithRole)),
                doc="List of users not created because of incompatibility with SSO.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "enrolled_users": to_dict(self.enrolled_users),
            "sso_incompatible_users": to_dict(self.sso_incompatible_users),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CourseBulkEnrollResult], d: t.Dict[str, t.Any]
    ) -> CourseBulkEnrollResult:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            enrolled_users=parsed.enrolled_users,
            sso_incompatible_users=parsed.sso_incompatible_users,
        )
        res.raw_data = d
        return res
