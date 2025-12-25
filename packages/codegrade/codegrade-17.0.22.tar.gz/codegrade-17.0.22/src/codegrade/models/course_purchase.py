"""The module that defines the ``CoursePurchase`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .base_purchase import BasePurchase
from .course_price import CoursePrice


@dataclass
class CoursePurchase(BasePurchase):
    """A course purchase by a user."""

    #: This was a purchase of a single course.
    scope: t.Literal["course"]
    #: The `CoursePrice` that this transaction pays for.
    purchased_item: CoursePrice

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BasePurchase.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "scope",
                    rqa.StringEnum("course"),
                    doc="This was a purchase of a single course.",
                ),
                rqa.RequiredArgument(
                    "purchased_item",
                    parsers.ParserFor.make(CoursePrice),
                    doc="The `CoursePrice` that this transaction pays for.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "scope": to_dict(self.scope),
            "purchased_item": to_dict(self.purchased_item),
            "id": to_dict(self.id),
            "state": to_dict(self.state),
            "success_at": to_dict(self.success_at),
            "updated_at": to_dict(self.updated_at),
            "short_id": to_dict(self.short_id),
            "item_purchase_iteration": to_dict(self.item_purchase_iteration),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CoursePurchase], d: t.Dict[str, t.Any]
    ) -> CoursePurchase:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            scope=parsed.scope,
            purchased_item=parsed.purchased_item,
            id=parsed.id,
            state=parsed.state,
            success_at=parsed.success_at,
            updated_at=parsed.updated_at,
            short_id=parsed.short_id,
            item_purchase_iteration=parsed.item_purchase_iteration,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime

    from .purchase_iteration import PurchaseIteration
    from .transaction_state import TransactionState
