"""The module that defines the ``PurchaseGrant`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .access_plan_purchase_summary import AccessPlanPurchaseSummary
from .course_purchase_summary import CoursePurchaseSummary


@dataclass
class PurchaseGrant:
    """Access was granted through a purchase."""

    #: The grant mechanism.
    type: t.Literal["purchase"]
    #: The purchase that granted the access.
    purchase: t.Union[AccessPlanPurchaseSummary, CoursePurchaseSummary]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "type",
                rqa.StringEnum("purchase"),
                doc="The grant mechanism.",
            ),
            rqa.RequiredArgument(
                "purchase",
                parsers.make_union(
                    parsers.ParserFor.make(AccessPlanPurchaseSummary),
                    parsers.ParserFor.make(CoursePurchaseSummary),
                ),
                doc="The purchase that granted the access.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "type": to_dict(self.type),
            "purchase": to_dict(self.purchase),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PurchaseGrant], d: t.Dict[str, t.Any]
    ) -> PurchaseGrant:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            type=parsed.type,
            purchase=parsed.purchase,
        )
        res.raw_data = d
        return res
