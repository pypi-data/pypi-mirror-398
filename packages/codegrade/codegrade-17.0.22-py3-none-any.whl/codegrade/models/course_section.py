"""The module that defines the ``CourseSection`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class CourseSection:
    """JSON representation of a course section."""

    #: The id of this section.
    id: str
    #: The name of this section.
    name: str
    #: The id of the course this section is connected to.
    course_id: int
    #: The number of members of this section.
    member_count: t.Optional[int]
    #: The ids of the members in the section.
    member_ids: t.Optional[t.Sequence[int]]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "id",
                rqa.SimpleValue.str,
                doc="The id of this section.",
            ),
            rqa.RequiredArgument(
                "name",
                rqa.SimpleValue.str,
                doc="The name of this section.",
            ),
            rqa.RequiredArgument(
                "course_id",
                rqa.SimpleValue.int,
                doc="The id of the course this section is connected to.",
            ),
            rqa.RequiredArgument(
                "member_count",
                rqa.Nullable(rqa.SimpleValue.int),
                doc="The number of members of this section.",
            ),
            rqa.RequiredArgument(
                "member_ids",
                rqa.Nullable(rqa.List(rqa.SimpleValue.int)),
                doc="The ids of the members in the section.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "name": to_dict(self.name),
            "course_id": to_dict(self.course_id),
            "member_count": to_dict(self.member_count),
            "member_ids": to_dict(self.member_ids),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CourseSection], d: t.Dict[str, t.Any]
    ) -> CourseSection:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            name=parsed.name,
            course_id=parsed.course_id,
            member_count=parsed.member_count,
            member_ids=parsed.member_ids,
        )
        res.raw_data = d
        return res
