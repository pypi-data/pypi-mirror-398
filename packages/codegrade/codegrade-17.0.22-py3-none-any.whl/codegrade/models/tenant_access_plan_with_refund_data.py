"""The module that defines the ``TenantAccessPlanWithRefundData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict
from .tenant_access_plan import TenantAccessPlan


@dataclass
class TenantAccessPlanWithRefundData(TenantAccessPlan):
    """Option to purchase access to all courses, with information on refund
    state.
    """

    #: Would this be a re-purchase for this access plan, since a refunded
    #: purchase exists that has not expired yet.
    is_repurchase: bool

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: TenantAccessPlan.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "is_repurchase",
                    rqa.SimpleValue.bool,
                    doc="Would this be a re-purchase for this access plan, since a refunded purchase exists that has not expired yet.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "is_repurchase": to_dict(self.is_repurchase),
            "tag": to_dict(self.tag),
            "duration": to_dict(self.duration),
            "tenant_id": to_dict(self.tenant_id),
            "id": to_dict(self.id),
            "currency": to_dict(self.currency),
            "amount": to_dict(self.amount),
            "refund_period": to_dict(self.refund_period),
            "tax_behavior": to_dict(self.tax_behavior),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[TenantAccessPlanWithRefundData], d: t.Dict[str, t.Any]
    ) -> TenantAccessPlanWithRefundData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            is_repurchase=parsed.is_repurchase,
            tag=parsed.tag,
            duration=parsed.duration,
            tenant_id=parsed.tenant_id,
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

    from .base_price import BasePrice
    from .currency import Currency
    from .tax_behavior import TaxBehavior
