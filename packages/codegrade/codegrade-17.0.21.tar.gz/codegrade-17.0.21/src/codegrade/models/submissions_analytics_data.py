"""The module that defines the ``SubmissionsAnalyticsData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class SubmissionsAnalyticsData:
    """The analytics for the general data of a submission."""

    #: This is submission data.
    tag: t.Literal["submission"]
    #: The author.
    user_id: int
    #: The moment the submission was created.
    created_at: datetime.datetime
    #: The grade it has.
    grade: t.Optional[float]
    #: The person it is assigned to.
    assignee_id: t.Optional[int]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "tag",
                rqa.StringEnum("submission"),
                doc="This is submission data.",
            ),
            rqa.RequiredArgument(
                "user_id",
                rqa.SimpleValue.int,
                doc="The author.",
            ),
            rqa.RequiredArgument(
                "created_at",
                rqa.RichValue.DateTime,
                doc="The moment the submission was created.",
            ),
            rqa.RequiredArgument(
                "grade",
                rqa.Nullable(rqa.SimpleValue.float),
                doc="The grade it has.",
            ),
            rqa.RequiredArgument(
                "assignee_id",
                rqa.Nullable(rqa.SimpleValue.int),
                doc="The person it is assigned to.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tag": to_dict(self.tag),
            "user_id": to_dict(self.user_id),
            "created_at": to_dict(self.created_at),
            "grade": to_dict(self.grade),
            "assignee_id": to_dict(self.assignee_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[SubmissionsAnalyticsData], d: t.Dict[str, t.Any]
    ) -> SubmissionsAnalyticsData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tag=parsed.tag,
            user_id=parsed.user_id,
            created_at=parsed.created_at,
            grade=parsed.grade,
            assignee_id=parsed.assignee_id,
        )
        res.raw_data = d
        return res
