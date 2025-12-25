"""The module that defines the ``Assignment`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .assignment_kind import AssignmentKind
from .assignment_restriction import AssignmentRestriction
from .fixed_grade_availability import FixedGradeAvailability
from .timeframe_like import TimeframeLike


@dataclass
class Assignment:
    """The serialization of an assignment.

    See the comments in the source code for the meaning of each field.
    """

    #: The id of the assignment.
    id: int
    #: The name of the assignment.
    name: str
    #: When this assignment was created.
    created_at: datetime.datetime
    #: The course this assignment belongs to.
    course_id: int
    #: Does this assignment have multiple timeframes.
    has_multiple_timeframes: bool
    #: Is this an LTI assignment.
    is_lti: bool
    #: Whether the assignment has liked description file.
    has_description: bool
    #: Whether the assignment is password restricted or not.
    restrictions: AssignmentRestriction
    #: Is the assignment available.
    timeframe: TimeframeLike
    #: What is grade availability of this assignment.
    grade_availability: FixedGradeAvailability
    #: What kind of assignment is this.
    kind: AssignmentKind

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "id",
                rqa.SimpleValue.int,
                doc="The id of the assignment.",
            ),
            rqa.RequiredArgument(
                "name",
                rqa.SimpleValue.str,
                doc="The name of the assignment.",
            ),
            rqa.RequiredArgument(
                "created_at",
                rqa.RichValue.DateTime,
                doc="When this assignment was created.",
            ),
            rqa.RequiredArgument(
                "course_id",
                rqa.SimpleValue.int,
                doc="The course this assignment belongs to.",
            ),
            rqa.RequiredArgument(
                "has_multiple_timeframes",
                rqa.SimpleValue.bool,
                doc="Does this assignment have multiple timeframes.",
            ),
            rqa.RequiredArgument(
                "is_lti",
                rqa.SimpleValue.bool,
                doc="Is this an LTI assignment.",
            ),
            rqa.RequiredArgument(
                "has_description",
                rqa.SimpleValue.bool,
                doc="Whether the assignment has liked description file.",
            ),
            rqa.RequiredArgument(
                "restrictions",
                parsers.ParserFor.make(AssignmentRestriction),
                doc="Whether the assignment is password restricted or not.",
            ),
            rqa.RequiredArgument(
                "timeframe",
                parsers.ParserFor.make(TimeframeLike),
                doc="Is the assignment available.",
            ),
            rqa.RequiredArgument(
                "grade_availability",
                parsers.ParserFor.make(FixedGradeAvailability),
                doc="What is grade availability of this assignment.",
            ),
            rqa.RequiredArgument(
                "kind",
                rqa.EnumValue(AssignmentKind),
                doc="What kind of assignment is this.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "name": to_dict(self.name),
            "created_at": to_dict(self.created_at),
            "course_id": to_dict(self.course_id),
            "has_multiple_timeframes": to_dict(self.has_multiple_timeframes),
            "is_lti": to_dict(self.is_lti),
            "has_description": to_dict(self.has_description),
            "restrictions": to_dict(self.restrictions),
            "timeframe": to_dict(self.timeframe),
            "grade_availability": to_dict(self.grade_availability),
            "kind": to_dict(self.kind),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[Assignment], d: t.Dict[str, t.Any]
    ) -> Assignment:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            name=parsed.name,
            created_at=parsed.created_at,
            course_id=parsed.course_id,
            has_multiple_timeframes=parsed.has_multiple_timeframes,
            is_lti=parsed.is_lti,
            has_description=parsed.has_description,
            restrictions=parsed.restrictions,
            timeframe=parsed.timeframe,
            grade_availability=parsed.grade_availability,
            kind=parsed.kind,
        )
        res.raw_data = d
        return res
