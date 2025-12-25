"""The module that defines the ``TenantAccessPlan`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict
from .base_price import BasePrice


@dataclass
class TenantAccessPlan(BasePrice):
    """The JSON representation of a TenantAccessPlan."""

    #: This is a access plan for a tenant.
    tag: t.Literal["tenant-access-plan"]
    #: The duration the pass would be active.
    duration: datetime.timedelta
    #: The id of the tenant for which the plan is.
    tenant_id: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BasePrice.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "tag",
                    rqa.StringEnum("tenant-access-plan"),
                    doc="This is a access plan for a tenant.",
                ),
                rqa.RequiredArgument(
                    "duration",
                    rqa.RichValue.TimeDelta,
                    doc="The duration the pass would be active.",
                ),
                rqa.RequiredArgument(
                    "tenant_id",
                    rqa.SimpleValue.str,
                    doc="The id of the tenant for which the plan is.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
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
        cls: t.Type[TenantAccessPlan], d: t.Dict[str, t.Any]
    ) -> TenantAccessPlan:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
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
    from .currency import Currency
    from .tax_behavior import TaxBehavior
