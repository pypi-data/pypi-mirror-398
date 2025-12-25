"""The module that defines the ``AssignmentGradebookSubmissionGrade`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class AssignmentGradebookSubmissionGrade:
    """Information pertaining to a single submission in the gradebook."""

    #: The id of the submission.
    submission_id: int
    #: The achieved grade.
    grade: t.Optional[float]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "submission_id",
                rqa.SimpleValue.int,
                doc="The id of the submission.",
            ),
            rqa.RequiredArgument(
                "grade",
                rqa.Nullable(rqa.SimpleValue.float),
                doc="The achieved grade.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "submission_id": to_dict(self.submission_id),
            "grade": to_dict(self.grade),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AssignmentGradebookSubmissionGrade], d: t.Dict[str, t.Any]
    ) -> AssignmentGradebookSubmissionGrade:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            submission_id=parsed.submission_id,
            grade=parsed.grade,
        )
        res.raw_data = d
        return res
