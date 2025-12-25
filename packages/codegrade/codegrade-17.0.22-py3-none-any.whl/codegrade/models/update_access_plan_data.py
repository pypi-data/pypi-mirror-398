"""The module that defines the ``UpdateAccessPlanData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict
from .base_access_plan_data import BaseAccessPlanData


@dataclass
class UpdateAccessPlanData(BaseAccessPlanData):
    """Data for updating a tenant access plan."""

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseAccessPlanData.data_parser.parser.combine(
            rqa.FixedMapping()
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "currency": to_dict(self.currency),
            "amount": to_dict(self.amount),
            "refund_period": to_dict(self.refund_period),
            "tax_behavior": to_dict(self.tax_behavior),
            "duration": to_dict(self.duration),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[UpdateAccessPlanData], d: t.Dict[str, t.Any]
    ) -> UpdateAccessPlanData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
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
