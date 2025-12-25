"""The module that defines the ``PaymentRequired`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .last_transaction_failure import LastTransactionFailure
from .payment_options import PaymentOptions


@dataclass
class PaymentRequired:
    """State when the user must pay to get access."""

    #: The top-level status tag.
    tag: t.Literal["payment-required"]
    #: The ways a user can pay.
    payment_options: PaymentOptions
    #: Optional details of a previous failed attempt.
    last_transaction_failure: t.Optional[LastTransactionFailure]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "tag",
                rqa.StringEnum("payment-required"),
                doc="The top-level status tag.",
            ),
            rqa.RequiredArgument(
                "payment_options",
                parsers.ParserFor.make(PaymentOptions),
                doc="The ways a user can pay.",
            ),
            rqa.RequiredArgument(
                "last_transaction_failure",
                rqa.Nullable(parsers.ParserFor.make(LastTransactionFailure)),
                doc="Optional details of a previous failed attempt.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tag": to_dict(self.tag),
            "payment_options": to_dict(self.payment_options),
            "last_transaction_failure": to_dict(self.last_transaction_failure),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PaymentRequired], d: t.Dict[str, t.Any]
    ) -> PaymentRequired:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tag=parsed.tag,
            payment_options=parsed.payment_options,
            last_transaction_failure=parsed.last_transaction_failure,
        )
        res.raw_data = d
        return res
