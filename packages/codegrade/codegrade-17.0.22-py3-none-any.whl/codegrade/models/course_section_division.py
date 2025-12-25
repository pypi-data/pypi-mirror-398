"""The module that defines the ``CourseSectionDivision`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .course_section_division_connection import CourseSectionDivisionConnection


@dataclass
class CourseSectionDivision:
    """JSON representation of a course section division."""

    #: The id of this division.
    id: str
    #: The users connected to this division.
    connections: t.Sequence[CourseSectionDivisionConnection]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "id",
                rqa.SimpleValue.str,
                doc="The id of this division.",
            ),
            rqa.RequiredArgument(
                "connections",
                rqa.List(
                    parsers.ParserFor.make(CourseSectionDivisionConnection)
                ),
                doc="The users connected to this division.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "connections": to_dict(self.connections),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CourseSectionDivision], d: t.Dict[str, t.Any]
    ) -> CourseSectionDivision:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            connections=parsed.connections,
        )
        res.raw_data = d
        return res
