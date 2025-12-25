"""The module that defines the ``BulkEnrollCourseData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .user_info_with_role import UserInfoWithRole


@dataclass
class BulkEnrollCourseData:
    """Input data required for the `Course::BulkEnroll` operation."""

    #: List of users to enroll into this course.
    users: t.Sequence[UserInfoWithRole]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "users",
                rqa.List(parsers.ParserFor.make(UserInfoWithRole)),
                doc="List of users to enroll into this course.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "users": to_dict(self.users),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[BulkEnrollCourseData], d: t.Dict[str, t.Any]
    ) -> BulkEnrollCourseData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            users=parsed.users,
        )
        res.raw_data = d
        return res
