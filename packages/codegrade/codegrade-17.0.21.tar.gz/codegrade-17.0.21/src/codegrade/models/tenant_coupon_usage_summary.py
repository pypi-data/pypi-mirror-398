"""The module that defines the ``TenantCouponUsageSummary`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict
from .base_coupon_usage_summary import BaseCouponUsageSummary


@dataclass
class TenantCouponUsageSummary(BaseCouponUsageSummary):
    """Usage of a tenant-wide coupon."""

    #: The scope the coupon was used on.
    scope: t.Literal["tenant"]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseCouponUsageSummary.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "scope",
                    rqa.StringEnum("tenant"),
                    doc="The scope the coupon was used on.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "scope": to_dict(self.scope),
            "id": to_dict(self.id),
            "success_at": to_dict(self.success_at),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[TenantCouponUsageSummary], d: t.Dict[str, t.Any]
    ) -> TenantCouponUsageSummary:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            scope=parsed.scope,
            id=parsed.id,
            success_at=parsed.success_at,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime
