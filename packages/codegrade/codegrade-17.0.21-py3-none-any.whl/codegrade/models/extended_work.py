"""The module that defines the ``ExtendedWork`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict
from .work import Work


@dataclass
class ExtendedWork(Work):
    """A submission in CodeGrade with extended data."""

    #: Is this the latest submission by this user.
    is_latest: bool

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: Work.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "is_latest",
                    rqa.SimpleValue.bool,
                    doc="Is this the latest submission by this user.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "is_latest": to_dict(self.is_latest),
            "id": to_dict(self.id),
            "user": to_dict(self.user),
            "origin": to_dict(self.origin),
            "created_at": to_dict(self.created_at),
            "manual_grading_status": to_dict(self.manual_grading_status),
            "grade": to_dict(self.grade),
            "assignee": to_dict(self.assignee),
            "grade_overridden": to_dict(self.grade_overridden),
            "extra_info": to_dict(self.extra_info),
            "timeframe": to_dict(self.timeframe),
            "assignment_id": to_dict(self.assignment_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[ExtendedWork], d: t.Dict[str, t.Any]
    ) -> ExtendedWork:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            is_latest=parsed.is_latest,
            id=parsed.id,
            user=parsed.user,
            origin=parsed.origin,
            created_at=parsed.created_at,
            manual_grading_status=parsed.manual_grading_status,
            grade=parsed.grade,
            assignee=parsed.assignee,
            grade_overridden=parsed.grade_overridden,
            extra_info=parsed.extra_info,
            timeframe=parsed.timeframe,
            assignment_id=parsed.assignment_id,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime

    from .timeframe_like import TimeframeLike
    from .user import User
    from .work_manual_grading_finished import WorkManualGradingFinished
    from .work_manual_grading_unfinished import WorkManualGradingUnfinished
    from .work_manual_grading_unknown import WorkManualGradingUnknown
    from .work_origin import WorkOrigin
