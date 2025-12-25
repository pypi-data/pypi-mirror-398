"""The module that defines the ``AccessPassCouponUsage`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .access_pass_coupon import AccessPassCoupon, AccessPassCouponParser
from .base_coupon_usage import BaseCouponUsage


@dataclass
class AccessPassCouponUsage(BaseCouponUsage):
    """ """

    #: This is a access pass coupon usage.
    scope: t.Literal["access-plan"]
    coupon: AccessPassCoupon

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseCouponUsage.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "scope",
                    rqa.StringEnum("access-plan"),
                    doc="This is a access pass coupon usage.",
                ),
                rqa.RequiredArgument(
                    "coupon",
                    AccessPassCouponParser,
                    doc="",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "scope": to_dict(self.scope),
            "coupon": to_dict(self.coupon),
            "id": to_dict(self.id),
            "success_at": to_dict(self.success_at),
            "user_id": to_dict(self.user_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AccessPassCouponUsage], d: t.Dict[str, t.Any]
    ) -> AccessPassCouponUsage:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            scope=parsed.scope,
            coupon=parsed.coupon,
            id=parsed.id,
            success_at=parsed.success_at,
            user_id=parsed.user_id,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime
