"""The module that defines the ``StartedTransaction`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class StartedTransaction:
    """What is returned after starting a new payment."""

    #: The URL of the payment provider that can be used to complete this
    #: transaction.
    payment_url: str
    #: The (future) ID of the transaction that was just started.
    transaction_id: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "payment_url",
                rqa.SimpleValue.str,
                doc="The URL of the payment provider that can be used to complete this transaction.",
            ),
            rqa.RequiredArgument(
                "transaction_id",
                rqa.SimpleValue.str,
                doc="The (future) ID of the transaction that was just started.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "payment_url": to_dict(self.payment_url),
            "transaction_id": to_dict(self.transaction_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[StartedTransaction], d: t.Dict[str, t.Any]
    ) -> StartedTransaction:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            payment_url=parsed.payment_url,
            transaction_id=parsed.transaction_id,
        )
        res.raw_data = d
        return res
