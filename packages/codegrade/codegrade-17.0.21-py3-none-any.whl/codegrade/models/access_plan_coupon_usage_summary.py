"""The module that defines the ``AccessPlanCouponUsageSummary`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .base_coupon_usage_summary import BaseCouponUsageSummary
from .tenant_access_plan import TenantAccessPlan


@dataclass
class AccessPlanCouponUsageSummary(BaseCouponUsageSummary):
    """Usage of an access plan coupon."""

    #: The scope the coupon was used on.
    scope: t.Literal["access-plan"]
    #: The specific, immutable plan object that was granted by the coupon.
    plan: TenantAccessPlan

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseCouponUsageSummary.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "scope",
                    rqa.StringEnum("access-plan"),
                    doc="The scope the coupon was used on.",
                ),
                rqa.RequiredArgument(
                    "plan",
                    parsers.ParserFor.make(TenantAccessPlan),
                    doc="The specific, immutable plan object that was granted by the coupon.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "scope": to_dict(self.scope),
            "plan": to_dict(self.plan),
            "id": to_dict(self.id),
            "success_at": to_dict(self.success_at),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AccessPlanCouponUsageSummary], d: t.Dict[str, t.Any]
    ) -> AccessPlanCouponUsageSummary:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            scope=parsed.scope,
            plan=parsed.plan,
            id=parsed.id,
            success_at=parsed.success_at,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime
