"""The module that defines the ``AssignmentSectionTimeframe`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict
from .timeframe_like import TimeframeLike


@dataclass
class AssignmentSectionTimeframe(TimeframeLike):
    """A section timeframe."""

    #: The id of the sections of this timeframe.
    section_ids: t.Sequence[str]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: TimeframeLike.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "section_ids",
                    rqa.List(rqa.SimpleValue.str),
                    doc="The id of the sections of this timeframe.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "section_ids": to_dict(self.section_ids),
            "availability": to_dict(self.availability),
            "deadline": to_dict(self.deadline),
            "lock_date": to_dict(self.lock_date),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AssignmentSectionTimeframe], d: t.Dict[str, t.Any]
    ) -> AssignmentSectionTimeframe:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            section_ids=parsed.section_ids,
            availability=parsed.availability,
            deadline=parsed.deadline,
            lock_date=parsed.lock_date,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime

    from .fixed_availability import FixedAvailability
    from .timed_availability import TimedAvailability
