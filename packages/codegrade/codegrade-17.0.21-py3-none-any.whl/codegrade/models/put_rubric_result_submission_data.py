"""The module that defines the ``PutRubricResultSubmissionData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from ._submission_rubric_item_data_parser import (
    _SubmissionRubricItemDataParser,
)


@dataclass
class PutRubricResultSubmissionData:
    """Input data required for the `Submission::PutRubricResult` operation."""

    #: An array of rubric items to select.
    items: t.Sequence[_SubmissionRubricItemDataParser]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "items",
                rqa.List(
                    parsers.ParserFor.make(_SubmissionRubricItemDataParser)
                ),
                doc="An array of rubric items to select.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "items": to_dict(self.items),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PutRubricResultSubmissionData], d: t.Dict[str, t.Any]
    ) -> PutRubricResultSubmissionData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            items=parsed.items,
        )
        res.raw_data = d
        return res
