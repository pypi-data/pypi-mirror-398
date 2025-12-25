"""The module that defines the ``TransactionDetails`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class TransactionDetails:
    """Details for a pending transaction."""

    #: Timestamp when the transaction was started.
    initiated_at: datetime.datetime
    #: The type of purchase being attempted.
    scope: t.Literal["access-plan", "course"]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "initiated_at",
                rqa.RichValue.DateTime,
                doc="Timestamp when the transaction was started.",
            ),
            rqa.RequiredArgument(
                "scope",
                rqa.StringEnum("access-plan", "course"),
                doc="The type of purchase being attempted.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "initiated_at": to_dict(self.initiated_at),
            "scope": to_dict(self.scope),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[TransactionDetails], d: t.Dict[str, t.Any]
    ) -> TransactionDetails:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            initiated_at=parsed.initiated_at,
            scope=parsed.scope,
        )
        res.raw_data = d
        return res
