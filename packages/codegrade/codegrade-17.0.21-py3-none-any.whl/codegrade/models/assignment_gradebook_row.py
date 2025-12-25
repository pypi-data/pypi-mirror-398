"""The module that defines the ``AssignmentGradebookRow`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .assignment_gradebook_submission_grade import (
    AssignmentGradebookSubmissionGrade,
)
from .normal_user import NormalUser


@dataclass
class AssignmentGradebookRow:
    """Representation of a single row in the output gradebook."""

    #: The user that got these grades.
    user: NormalUser
    #: The grade this user got.
    grade: AssignmentGradebookSubmissionGrade

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "user",
                parsers.ParserFor.make(NormalUser),
                doc="The user that got these grades.",
            ),
            rqa.RequiredArgument(
                "grade",
                parsers.ParserFor.make(AssignmentGradebookSubmissionGrade),
                doc="The grade this user got.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "user": to_dict(self.user),
            "grade": to_dict(self.grade),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AssignmentGradebookRow], d: t.Dict[str, t.Any]
    ) -> AssignmentGradebookRow:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            user=parsed.user,
            grade=parsed.grade,
        )
        res.raw_data = d
        return res
