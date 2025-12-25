"""The module that defines the ``PatchSubmissionData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from ..utils import to_dict


@dataclass
class PatchSubmissionData:
    """Input data required for the `Submission::Patch` operation."""

    #: The grade of the submission.
    grade: Maybe[t.Optional[float]] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.OptionalArgument(
                "grade",
                rqa.Nullable(rqa.SimpleValue.float),
                doc="The grade of the submission.",
            ),
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.grade = maybe_from_nullable(self.grade)

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {}
        if self.grade.is_just:
            res["grade"] = to_dict(self.grade.value)
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PatchSubmissionData], d: t.Dict[str, t.Any]
    ) -> PatchSubmissionData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            grade=parsed.grade,
        )
        res.raw_data = d
        return res
