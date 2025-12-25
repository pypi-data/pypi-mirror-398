"""The module that defines the ``WorkCommentCount`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class WorkCommentCount:
    """The number of replies a user made on a single submission."""

    #: The ID of the work (submission) the replies were on.
    work_id: int
    #: The total count of replies made by the user on this work.
    reply_count: int

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "work_id",
                rqa.SimpleValue.int,
                doc="The ID of the work (submission) the replies were on.",
            ),
            rqa.RequiredArgument(
                "reply_count",
                rqa.SimpleValue.int,
                doc="The total count of replies made by the user on this work.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "work_id": to_dict(self.work_id),
            "reply_count": to_dict(self.reply_count),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[WorkCommentCount], d: t.Dict[str, t.Any]
    ) -> WorkCommentCount:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            work_id=parsed.work_id,
            reply_count=parsed.reply_count,
        )
        res.raw_data = d
        return res
