"""The module that defines the ``WorkRubricItem`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class WorkRubricItem:
    """The connection between a submission and a rubric item."""

    #: The id of the item that was selected.
    item_id: int
    #: The multiplier of this rubric item. This is especially useful for
    #: continuous rows, if a user achieved 50% of the points this will 0.5 for
    #: that rubric row.
    multiplier: float
    #: The amount of achieved points in this rubric item. This is simply the
    #: `points` field multiplied by the `multiplier` field.
    achieved_points: float

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "item_id",
                rqa.SimpleValue.int,
                doc="The id of the item that was selected.",
            ),
            rqa.RequiredArgument(
                "multiplier",
                rqa.SimpleValue.float,
                doc="The multiplier of this rubric item. This is especially useful for continuous rows, if a user achieved 50% of the points this will 0.5 for that rubric row.",
            ),
            rqa.RequiredArgument(
                "achieved_points",
                rqa.SimpleValue.float,
                doc="The amount of achieved points in this rubric item. This is simply the `points` field multiplied by the `multiplier` field.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "item_id": to_dict(self.item_id),
            "multiplier": to_dict(self.multiplier),
            "achieved_points": to_dict(self.achieved_points),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[WorkRubricItem], d: t.Dict[str, t.Any]
    ) -> WorkRubricItem:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            item_id=parsed.item_id,
            multiplier=parsed.multiplier,
            achieved_points=parsed.achieved_points,
        )
        res.raw_data = d
        return res
