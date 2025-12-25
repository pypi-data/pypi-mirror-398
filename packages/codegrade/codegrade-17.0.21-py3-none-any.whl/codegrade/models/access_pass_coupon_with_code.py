"""The module that defines the ``AccessPassCouponWithCode`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .base_coupon_with_code import BaseCouponWithCode
from .tenant_access_plan import TenantAccessPlan


@dataclass
class AccessPassCouponWithCode(BaseCouponWithCode):
    """A coupon where you do have the permission to see the code."""

    #: The scope of validity of the coupon. Used to discriminate from Coupon.
    scope: t.Literal["access-plan"]
    #: The plan this is a coupon for.
    plan: TenantAccessPlan

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseCouponWithCode.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "scope",
                    rqa.StringEnum("access-plan"),
                    doc="The scope of validity of the coupon. Used to discriminate from Coupon.",
                ),
                rqa.RequiredArgument(
                    "plan",
                    parsers.ParserFor.make(TenantAccessPlan),
                    doc="The plan this is a coupon for.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "scope": to_dict(self.scope),
            "plan": to_dict(self.plan),
            "type": to_dict(self.type),
            "code": to_dict(self.code),
            "id": to_dict(self.id),
            "created_at": to_dict(self.created_at),
            "limit": to_dict(self.limit),
            "used_amount": to_dict(self.used_amount),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AccessPassCouponWithCode], d: t.Dict[str, t.Any]
    ) -> AccessPassCouponWithCode:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            scope=parsed.scope,
            plan=parsed.plan,
            type=parsed.type,
            code=parsed.code,
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
