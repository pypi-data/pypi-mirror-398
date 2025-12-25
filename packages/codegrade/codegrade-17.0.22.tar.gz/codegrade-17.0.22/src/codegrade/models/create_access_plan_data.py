"""The module that defines the ``CreateAccessPlanData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict
from .base_access_plan_data import BaseAccessPlanData


@dataclass
class CreateAccessPlanData(BaseAccessPlanData):
    """Data for creating a tenant access plan."""

    #: The id of the tenant to create the plan for.
    tenant_id: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseAccessPlanData.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "tenant_id",
                    rqa.SimpleValue.str,
                    doc="The id of the tenant to create the plan for.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tenant_id": to_dict(self.tenant_id),
            "currency": to_dict(self.currency),
            "amount": to_dict(self.amount),
            "refund_period": to_dict(self.refund_period),
            "tax_behavior": to_dict(self.tax_behavior),
            "duration": to_dict(self.duration),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CreateAccessPlanData], d: t.Dict[str, t.Any]
    ) -> CreateAccessPlanData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tenant_id=parsed.tenant_id,
            currency=parsed.currency,
            amount=parsed.amount,
            refund_period=parsed.refund_period,
            tax_behavior=parsed.tax_behavior,
            duration=parsed.duration,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime

    from .currency import Currency
    from .tax_behavior import TaxBehavior
