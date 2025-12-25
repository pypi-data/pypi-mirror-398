"""The module that defines the ``TimedAvailability`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class TimedAvailability:
    """The availability is dependent on the time."""

    #: The tag for this data.
    tag: t.Literal["timed"]
    #: The moment the assignment will become available.
    available_at: datetime.datetime

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "tag",
                rqa.StringEnum("timed"),
                doc="The tag for this data.",
            ),
            rqa.RequiredArgument(
                "available_at",
                rqa.RichValue.DateTime,
                doc="The moment the assignment will become available.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tag": to_dict(self.tag),
            "available_at": to_dict(self.available_at),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[TimedAvailability], d: t.Dict[str, t.Any]
    ) -> TimedAvailability:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tag=parsed.tag,
            available_at=parsed.available_at,
        )
        res.raw_data = d
        return res
