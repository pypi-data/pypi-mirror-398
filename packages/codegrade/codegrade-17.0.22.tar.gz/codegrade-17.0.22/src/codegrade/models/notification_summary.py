"""The module that defines the ``NotificationSummary`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class NotificationSummary:
    """A summary of notification counts for a user."""

    #: The number of unread notifications, capped at 10 as maximum.
    unread_count: int

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "unread_count",
                rqa.SimpleValue.int,
                doc="The number of unread notifications, capped at 10 as maximum.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "unread_count": to_dict(self.unread_count),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[NotificationSummary], d: t.Dict[str, t.Any]
    ) -> NotificationSummary:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            unread_count=parsed.unread_count,
        )
        res.raw_data = d
        return res
