"""The module that defines the ``TenantCouponUsage`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .base_coupon_usage import BaseCouponUsage
from .course_of_tenant_coupon_usage import CourseOfTenantCouponUsage
from .tenant_coupon import TenantCoupon, TenantCouponParser


@dataclass
class TenantCouponUsage(BaseCouponUsage):
    """A link that represents the usage of a coupon by a user."""

    #: The scope of the coupon usage
    scope: t.Literal["tenant"]
    coupon: TenantCoupon
    #: The course for which the coupon was used.
    course: CourseOfTenantCouponUsage

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseCouponUsage.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "scope",
                    rqa.StringEnum("tenant"),
                    doc="The scope of the coupon usage",
                ),
                rqa.RequiredArgument(
                    "coupon",
                    TenantCouponParser,
                    doc="",
                ),
                rqa.RequiredArgument(
                    "course",
                    parsers.ParserFor.make(CourseOfTenantCouponUsage),
                    doc="The course for which the coupon was used.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "scope": to_dict(self.scope),
            "coupon": to_dict(self.coupon),
            "course": to_dict(self.course),
            "id": to_dict(self.id),
            "success_at": to_dict(self.success_at),
            "user_id": to_dict(self.user_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[TenantCouponUsage], d: t.Dict[str, t.Any]
    ) -> TenantCouponUsage:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            scope=parsed.scope,
            coupon=parsed.coupon,
            course=parsed.course,
            id=parsed.id,
            success_at=parsed.success_at,
            user_id=parsed.user_id,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime
