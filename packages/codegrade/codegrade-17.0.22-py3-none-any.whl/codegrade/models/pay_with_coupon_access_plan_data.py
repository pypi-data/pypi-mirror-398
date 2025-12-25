"""The module that defines the ``PayWithCouponAccessPlanData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class PayWithCouponAccessPlanData:
    """Input data required for the `Access Plan::PayWithCoupon` operation."""

    #: The coupon code to use
    code: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "code",
                rqa.SimpleValue.str,
                doc="The coupon code to use",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "code": to_dict(self.code),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PayWithCouponAccessPlanData], d: t.Dict[str, t.Any]
    ) -> PayWithCouponAccessPlanData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            code=parsed.code,
        )
        res.raw_data = d
        return res
