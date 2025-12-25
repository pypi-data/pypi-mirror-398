"""The module that defines the ``AssignmentPointsGradingSettings`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .fraction import Fraction


@dataclass
class AssignmentPointsGradingSettings:
    """Representation of the points grading settings of an assignment."""

    #: The scale on which this assignment is graded. 'points' means that a
    #: number of points between 0 and `points` (inclusive) can be scored.
    scale: t.Literal["points"]
    #: The maximum grade for point-based scales.
    points: Fraction

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "scale",
                rqa.StringEnum("points"),
                doc="The scale on which this assignment is graded. 'points' means that a number of points between 0 and `points` (inclusive) can be scored.",
            ),
            rqa.RequiredArgument(
                "points",
                parsers.ParserFor.make(Fraction),
                doc="The maximum grade for point-based scales.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "scale": to_dict(self.scale),
            "points": to_dict(self.points),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AssignmentPointsGradingSettings], d: t.Dict[str, t.Any]
    ) -> AssignmentPointsGradingSettings:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            scale=parsed.scale,
            points=parsed.points,
        )
        res.raw_data = d
        return res
