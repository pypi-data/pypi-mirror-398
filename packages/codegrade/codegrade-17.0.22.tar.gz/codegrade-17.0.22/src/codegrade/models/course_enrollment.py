"""The module that defines the ``CourseEnrollment`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .course_role import CourseRole
from .user import User, UserParser


@dataclass
class CourseEnrollment:
    """A user and their role in a course."""

    user: User
    #: The role they have in the course.
    course_role: CourseRole

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "user",
                UserParser,
                doc="",
            ),
            rqa.RequiredArgument(
                "course_role",
                parsers.ParserFor.make(CourseRole),
                doc="The role they have in the course.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "user": to_dict(self.user),
            "course_role": to_dict(self.course_role),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CourseEnrollment], d: t.Dict[str, t.Any]
    ) -> CourseEnrollment:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            user=parsed.user,
            course_role=parsed.course_role,
        )
        res.raw_data = d
        return res
