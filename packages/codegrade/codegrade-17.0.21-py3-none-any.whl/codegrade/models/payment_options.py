"""The module that defines the ``PaymentOptions`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .course_price_with_refund_data import CoursePriceWithRefundData
from .tenant_access_plan_with_refund_data import TenantAccessPlanWithRefundData


@dataclass
class PaymentOptions:
    """Defines all available ways a user can pay, using existing domain models."""

    #: The available course price, if direct purchase is an option.
    course_purchase: t.Optional[CoursePriceWithRefundData]
    #: A list of available tenant access plans.
    access_plans: t.Sequence[TenantAccessPlanWithRefundData]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "course_purchase",
                rqa.Nullable(
                    parsers.ParserFor.make(CoursePriceWithRefundData)
                ),
                doc="The available course price, if direct purchase is an option.",
            ),
            rqa.RequiredArgument(
                "access_plans",
                rqa.List(
                    parsers.ParserFor.make(TenantAccessPlanWithRefundData)
                ),
                doc="A list of available tenant access plans.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "course_purchase": to_dict(self.course_purchase),
            "access_plans": to_dict(self.access_plans),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PaymentOptions], d: t.Dict[str, t.Any]
    ) -> PaymentOptions:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            course_purchase=parsed.course_purchase,
            access_plans=parsed.access_plans,
        )
        res.raw_data = d
        return res
