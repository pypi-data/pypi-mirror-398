"""The module that defines the ``InlineFeedbackAnalyticsData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class InlineFeedbackAnalyticsData:
    """The analytics for inline feedback."""

    #: This is inline feedback data.
    tag: t.Literal["inline-feedback"]
    #: The total amount of inline feedback comments.
    total_amount: int

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "tag",
                rqa.StringEnum("inline-feedback"),
                doc="This is inline feedback data.",
            ),
            rqa.RequiredArgument(
                "total_amount",
                rqa.SimpleValue.int,
                doc="The total amount of inline feedback comments.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tag": to_dict(self.tag),
            "total_amount": to_dict(self.total_amount),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[InlineFeedbackAnalyticsData], d: t.Dict[str, t.Any]
    ) -> InlineFeedbackAnalyticsData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tag=parsed.tag,
            total_amount=parsed.total_amount,
        )
        res.raw_data = d
        return res
