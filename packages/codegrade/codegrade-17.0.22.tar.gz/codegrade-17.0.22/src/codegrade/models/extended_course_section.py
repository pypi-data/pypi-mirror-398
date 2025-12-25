"""The module that defines the ``ExtendedCourseSection`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .course_section import CourseSection
from .user import User, UserParser


@dataclass
class ExtendedCourseSection(CourseSection):
    """Extended JSON representation of a course section."""

    #: The members of this course section.
    members: t.Optional[t.Sequence[User]]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: CourseSection.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "members",
                    rqa.Nullable(rqa.List(UserParser)),
                    doc="The members of this course section.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "members": to_dict(self.members),
            "id": to_dict(self.id),
            "name": to_dict(self.name),
            "course_id": to_dict(self.course_id),
            "member_count": to_dict(self.member_count),
            "member_ids": to_dict(self.member_ids),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[ExtendedCourseSection], d: t.Dict[str, t.Any]
    ) -> ExtendedCourseSection:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            members=parsed.members,
            id=parsed.id,
            name=parsed.name,
            course_id=parsed.course_id,
            member_count=parsed.member_count,
            member_ids=parsed.member_ids,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    pass
