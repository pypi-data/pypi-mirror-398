"""The module that defines the ``BasePurchase`` model.

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
from .transaction_state import TransactionState


@dataclass
class BasePurchase:
    """Any purchase by a user."""

    #: The id of the transaction.
    id: str
    #: The state of the transaction.
    state: TransactionState
    #: The moment the payment was successful, this will always be not `None`
    #: when `state` is `success`.
    success_at: t.Optional[datetime.datetime]
    #: The moment this transaction was last updated.
    updated_at: datetime.datetime
    #: The short id of the transaction.
    short_id: str
    #: Whether this purchase is a repurchase for a previously refunded
    #: purchased item.
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
                "state",
                rqa.EnumValue(TransactionState),
                doc="The state of the transaction.",
            ),
            rqa.RequiredArgument(
                "success_at",
                rqa.Nullable(rqa.RichValue.DateTime),
                doc="The moment the payment was successful, this will always be not `None` when `state` is `success`.",
            ),
            rqa.RequiredArgument(
                "updated_at",
                rqa.RichValue.DateTime,
                doc="The moment this transaction was last updated.",
            ),
            rqa.RequiredArgument(
                "short_id",
                rqa.SimpleValue.str,
                doc="The short id of the transaction.",
            ),
            rqa.RequiredArgument(
                "item_purchase_iteration",
                rqa.EnumValue(PurchaseIteration),
                doc="Whether this purchase is a repurchase for a previously refunded purchased item.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "state": to_dict(self.state),
            "success_at": to_dict(self.success_at),
            "updated_at": to_dict(self.updated_at),
            "short_id": to_dict(self.short_id),
            "item_purchase_iteration": to_dict(self.item_purchase_iteration),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[BasePurchase], d: t.Dict[str, t.Any]
    ) -> BasePurchase:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            state=parsed.state,
            success_at=parsed.success_at,
            updated_at=parsed.updated_at,
            short_id=parsed.short_id,
            item_purchase_iteration=parsed.item_purchase_iteration,
        )
        res.raw_data = d
        return res
