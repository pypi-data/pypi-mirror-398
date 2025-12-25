"""The module that defines the ``CreateDivisionResult`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .course_section_division import CourseSectionDivision
from .extended_course_section import ExtendedCourseSection


@dataclass
class CreateDivisionResult:
    """The result of creating a section division, containing the new division
    and the updated section.
    """

    #: The updated course section.
    section: ExtendedCourseSection
    #: The created section division.
    division: CourseSectionDivision

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "section",
                parsers.ParserFor.make(ExtendedCourseSection),
                doc="The updated course section.",
            ),
            rqa.RequiredArgument(
                "division",
                parsers.ParserFor.make(CourseSectionDivision),
                doc="The created section division.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "section": to_dict(self.section),
            "division": to_dict(self.division),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CreateDivisionResult], d: t.Dict[str, t.Any]
    ) -> CreateDivisionResult:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            section=parsed.section,
            division=parsed.division,
        )
        res.raw_data = d
        return res
