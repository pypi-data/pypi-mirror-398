"""The module that defines the ``BaseAccessPlanData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .currency import Currency
from .tax_behavior import TaxBehavior


@dataclass
class BaseAccessPlanData:
    """Data for creating/updating a tenant access plan."""

    #: The currency for the access pass.
    currency: Currency
    #: The price of the tenant-wide access pass.
    amount: str
    #: The period during which a refund can be requested for the pass.
    refund_period: datetime.timedelta
    #: How tax should be handled for the price.
    tax_behavior: TaxBehavior
    #: The duration for which the access pass is valid.
    duration: datetime.timedelta

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "currency",
                rqa.EnumValue(Currency),
                doc="The currency for the access pass.",
            ),
            rqa.RequiredArgument(
                "amount",
                rqa.SimpleValue.str,
                doc="The price of the tenant-wide access pass.",
            ),
            rqa.RequiredArgument(
                "refund_period",
                rqa.RichValue.TimeDelta,
                doc="The period during which a refund can be requested for the pass.",
            ),
            rqa.RequiredArgument(
                "tax_behavior",
                rqa.EnumValue(TaxBehavior),
                doc="How tax should be handled for the price.",
            ),
            rqa.RequiredArgument(
                "duration",
                rqa.RichValue.TimeDelta,
                doc="The duration for which the access pass is valid.",
            ),
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
        cls: t.Type[BaseAccessPlanData], d: t.Dict[str, t.Any]
    ) -> BaseAccessPlanData:
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
