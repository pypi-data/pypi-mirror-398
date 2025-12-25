"""The module that defines the ``CouponGrant`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .access_plan_coupon_usage_summary import AccessPlanCouponUsageSummary
from .course_coupon_usage_summary import CourseCouponUsageSummary
from .tenant_coupon_usage_summary import TenantCouponUsageSummary


@dataclass
class CouponGrant:
    """Access was granted through a coupon."""

    #: The grant mechanism.
    type: t.Literal["coupon"]
    #: The coupon usage that granted access.
    coupon: t.Union[
        AccessPlanCouponUsageSummary,
        CourseCouponUsageSummary,
        TenantCouponUsageSummary,
    ]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "type",
                rqa.StringEnum("coupon"),
                doc="The grant mechanism.",
            ),
            rqa.RequiredArgument(
                "coupon",
                parsers.make_union(
                    parsers.ParserFor.make(AccessPlanCouponUsageSummary),
                    parsers.ParserFor.make(CourseCouponUsageSummary),
                    parsers.ParserFor.make(TenantCouponUsageSummary),
                ),
                doc="The coupon usage that granted access.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "type": to_dict(self.type),
            "coupon": to_dict(self.coupon),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CouponGrant], d: t.Dict[str, t.Any]
    ) -> CouponGrant:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            type=parsed.type,
            coupon=parsed.coupon,
        )
        res.raw_data = d
        return res
