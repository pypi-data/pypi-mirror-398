"""The module that defines the ``TimeframeLike`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .fixed_availability import FixedAvailability
from .timed_availability import TimedAvailability


@dataclass
class TimeframeLike:
    """A timeframe of an assignment."""

    #: What is the availability state of this assignment.
    availability: t.Union[FixedAvailability, TimedAvailability]
    #: The deadline of the assignment. It is possible the assignment has no
    #: deadline yet, in which case it will be `None`.
    deadline: t.Optional[datetime.datetime]
    #: The moment this assignment locks, this can be seen as a form of second
    #: deadline.
    lock_date: t.Optional[datetime.datetime]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "availability",
                parsers.make_union(
                    parsers.ParserFor.make(FixedAvailability),
                    parsers.ParserFor.make(TimedAvailability),
                ),
                doc="What is the availability state of this assignment.",
            ),
            rqa.RequiredArgument(
                "deadline",
                rqa.Nullable(rqa.RichValue.DateTime),
                doc="The deadline of the assignment. It is possible the assignment has no deadline yet, in which case it will be `None`.",
            ),
            rqa.RequiredArgument(
                "lock_date",
                rqa.Nullable(rqa.RichValue.DateTime),
                doc="The moment this assignment locks, this can be seen as a form of second deadline.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "availability": to_dict(self.availability),
            "deadline": to_dict(self.deadline),
            "lock_date": to_dict(self.lock_date),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[TimeframeLike], d: t.Dict[str, t.Any]
    ) -> TimeframeLike:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            availability=parsed.availability,
            deadline=parsed.deadline,
            lock_date=parsed.lock_date,
        )
        res.raw_data = d
        return res
