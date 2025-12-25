"""The module that defines the ``AssignmentGrader`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict
from .normal_user import NormalUser


@dataclass
class AssignmentGrader(NormalUser):
    """A grader for an assignment."""

    #: The division weight of the grader, if no division is setup this will be
    #: 0.
    weight: float
    #: Did this grader indicate that grading has finished? NOTE: This field
    #: will be removed or changed in a future release.
    done: bool

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: NormalUser.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "weight",
                    rqa.SimpleValue.float,
                    doc="The division weight of the grader, if no division is setup this will be 0.",
                ),
                rqa.RequiredArgument(
                    "done",
                    rqa.SimpleValue.bool,
                    doc="Did this grader indicate that grading has finished? NOTE: This field will be removed or changed in a future release.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "weight": to_dict(self.weight),
            "done": to_dict(self.done),
            "type": to_dict(self.type),
            "name": to_dict(self.name),
            "is_test_student": to_dict(self.is_test_student),
            "id": to_dict(self.id),
            "username": to_dict(self.username),
            "tenant_id": to_dict(self.tenant_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AssignmentGrader], d: t.Dict[str, t.Any]
    ) -> AssignmentGrader:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            weight=parsed.weight,
            done=parsed.done,
            type=parsed.type,
            name=parsed.name,
            is_test_student=parsed.is_test_student,
            id=parsed.id,
            username=parsed.username,
            tenant_id=parsed.tenant_id,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    from .base_user import BaseUser
