"""The module that defines the ``CouponWithoutCode`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .base_coupon_without_code import BaseCouponWithoutCode
from .course_price import CoursePrice


@dataclass
class CouponWithoutCode(BaseCouponWithoutCode):
    """A coupon where you don't have the permission to see the code."""

    #: The scope of validity of the coupon. Used to discriminate from Coupon.
    scope: t.Literal["course"]
    #: The `CoursePrice` this coupon pays for.
    course_price: CoursePrice

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseCouponWithoutCode.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "scope",
                    rqa.StringEnum("course"),
                    doc="The scope of validity of the coupon. Used to discriminate from Coupon.",
                ),
                rqa.RequiredArgument(
                    "course_price",
                    parsers.ParserFor.make(CoursePrice),
                    doc="The `CoursePrice` this coupon pays for.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "scope": to_dict(self.scope),
            "course_price": to_dict(self.course_price),
            "type": to_dict(self.type),
            "id": to_dict(self.id),
            "created_at": to_dict(self.created_at),
            "limit": to_dict(self.limit),
            "used_amount": to_dict(self.used_amount),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CouponWithoutCode], d: t.Dict[str, t.Any]
    ) -> CouponWithoutCode:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            scope=parsed.scope,
            course_price=parsed.course_price,
            type=parsed.type,
            id=parsed.id,
            created_at=parsed.created_at,
            limit=parsed.limit,
            used_amount=parsed.used_amount,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime

    from .base_coupon import BaseCoupon
