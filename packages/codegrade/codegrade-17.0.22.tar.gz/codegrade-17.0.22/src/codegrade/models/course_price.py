"""The module that defines the ``CoursePrice`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .base_price import BasePrice
from .course_of_course_price import CourseOfCoursePrice


@dataclass
class CoursePrice(BasePrice):
    """The price of a single course."""

    #: This is a price for a course.
    tag: t.Literal["course-price"]
    #: The course that is connected to this price.
    course: CourseOfCoursePrice
    #: Is this price still editable.
    editable: bool

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BasePrice.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "tag",
                    rqa.StringEnum("course-price"),
                    doc="This is a price for a course.",
                ),
                rqa.RequiredArgument(
                    "course",
                    parsers.ParserFor.make(CourseOfCoursePrice),
                    doc="The course that is connected to this price.",
                ),
                rqa.RequiredArgument(
                    "editable",
                    rqa.SimpleValue.bool,
                    doc="Is this price still editable.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tag": to_dict(self.tag),
            "course": to_dict(self.course),
            "editable": to_dict(self.editable),
            "id": to_dict(self.id),
            "currency": to_dict(self.currency),
            "amount": to_dict(self.amount),
            "refund_period": to_dict(self.refund_period),
            "tax_behavior": to_dict(self.tax_behavior),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CoursePrice], d: t.Dict[str, t.Any]
    ) -> CoursePrice:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tag=parsed.tag,
            course=parsed.course,
            editable=parsed.editable,
            id=parsed.id,
            currency=parsed.currency,
            amount=parsed.amount,
            refund_period=parsed.refund_period,
            tax_behavior=parsed.tax_behavior,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime

    from .currency import Currency
    from .tax_behavior import TaxBehavior
