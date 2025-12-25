"""The module that defines the ``BasePurchaseSummary`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .purchase_iteration import PurchaseIteration


@dataclass
class BasePurchaseSummary:
    """Shared fields across all purchase summary types."""

    #: The id of the transaction.
    id: str
    #: Timestamp when this purchase was successful.
    success_at: datetime.datetime
    #: Which purchase iteration for the exact purchased_item this is.
    item_purchase_iteration: PurchaseIteration

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "id",
                rqa.SimpleValue.str,
                doc="The id of the transaction.",
            ),
            rqa.RequiredArgument(
                "success_at",
                rqa.RichValue.DateTime,
                doc="Timestamp when this purchase was successful.",
            ),
            rqa.RequiredArgument(
                "item_purchase_iteration",
                rqa.EnumValue(PurchaseIteration),
                doc="Which purchase iteration for the exact purchased_item this is.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "success_at": to_dict(self.success_at),
            "item_purchase_iteration": to_dict(self.item_purchase_iteration),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[BasePurchaseSummary], d: t.Dict[str, t.Any]
    ) -> BasePurchaseSummary:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            success_at=parsed.success_at,
            item_purchase_iteration=parsed.item_purchase_iteration,
        )
        res.raw_data = d
        return res
