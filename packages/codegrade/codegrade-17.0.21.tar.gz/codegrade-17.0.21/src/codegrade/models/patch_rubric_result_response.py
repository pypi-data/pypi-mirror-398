"""The module that defines the ``PatchRubricResultResponse`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .extended_work import ExtendedWork
from .work_rubric_item import WorkRubricItem


@dataclass
class PatchRubricResultResponse:
    """The result after updating the rubric of a submission."""

    #: The, locked, items that were copied.
    copied_items: t.Sequence[WorkRubricItem]
    #: The new grade of the submission.
    submission: ExtendedWork

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "copied_items",
                rqa.List(parsers.ParserFor.make(WorkRubricItem)),
                doc="The, locked, items that were copied.",
            ),
            rqa.RequiredArgument(
                "submission",
                parsers.ParserFor.make(ExtendedWork),
                doc="The new grade of the submission.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "copied_items": to_dict(self.copied_items),
            "submission": to_dict(self.submission),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PatchRubricResultResponse], d: t.Dict[str, t.Any]
    ) -> PatchRubricResultResponse:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            copied_items=parsed.copied_items,
            submission=parsed.submission,
        )
        res.raw_data = d
        return res
