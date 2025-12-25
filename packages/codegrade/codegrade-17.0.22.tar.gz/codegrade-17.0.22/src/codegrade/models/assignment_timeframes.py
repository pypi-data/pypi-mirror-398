"""The module that defines the ``AssignmentTimeframes`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .assignment_section_timeframe import AssignmentSectionTimeframe
from .timeframe_like import TimeframeLike


@dataclass
class AssignmentTimeframes:
    """The timeframe of an assignment."""

    #: The general timeframe.
    general: TimeframeLike
    #: The timeframe overrides for sections.
    sections: t.Sequence[AssignmentSectionTimeframe]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "general",
                parsers.ParserFor.make(TimeframeLike),
                doc="The general timeframe.",
            ),
            rqa.RequiredArgument(
                "sections",
                rqa.List(parsers.ParserFor.make(AssignmentSectionTimeframe)),
                doc="The timeframe overrides for sections.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "general": to_dict(self.general),
            "sections": to_dict(self.sections),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AssignmentTimeframes], d: t.Dict[str, t.Any]
    ) -> AssignmentTimeframes:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            general=parsed.general,
            sections=parsed.sections,
        )
        res.raw_data = d
        return res
