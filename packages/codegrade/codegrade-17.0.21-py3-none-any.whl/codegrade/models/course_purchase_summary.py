"""The module that defines the ``CoursePurchaseSummary`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .base_purchase_summary import BasePurchaseSummary
from .course_price import CoursePrice


@dataclass
class CoursePurchaseSummary(BasePurchaseSummary):
    """A summary of a direct course purchase."""

    #: The scope of the purchase.
    scope: t.Literal["course"]
    #: The specific, immutable price object that was purchased.
    purchased_item: CoursePrice

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BasePurchaseSummary.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "scope",
                    rqa.StringEnum("course"),
                    doc="The scope of the purchase.",
                ),
                rqa.RequiredArgument(
                    "purchased_item",
                    parsers.ParserFor.make(CoursePrice),
                    doc="The specific, immutable price object that was purchased.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "scope": to_dict(self.scope),
            "purchased_item": to_dict(self.purchased_item),
            "id": to_dict(self.id),
            "success_at": to_dict(self.success_at),
            "item_purchase_iteration": to_dict(self.item_purchase_iteration),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CoursePurchaseSummary], d: t.Dict[str, t.Any]
    ) -> CoursePurchaseSummary:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            scope=parsed.scope,
            purchased_item=parsed.purchased_item,
            id=parsed.id,
            success_at=parsed.success_at,
            item_purchase_iteration=parsed.item_purchase_iteration,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime

    from .purchase_iteration import PurchaseIteration
