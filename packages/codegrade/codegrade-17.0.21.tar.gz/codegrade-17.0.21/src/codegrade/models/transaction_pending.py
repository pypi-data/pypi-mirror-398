"""The module that defines the ``TransactionPending`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .transaction_details import TransactionDetails


@dataclass
class TransactionPending:
    """State when a payment is currently being processed."""

    #: The top-level status tag.
    tag: t.Literal["transaction-pending"]
    #: Information about the in-progress transaction.
    details: TransactionDetails

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "tag",
                rqa.StringEnum("transaction-pending"),
                doc="The top-level status tag.",
            ),
            rqa.RequiredArgument(
                "details",
                parsers.ParserFor.make(TransactionDetails),
                doc="Information about the in-progress transaction.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tag": to_dict(self.tag),
            "details": to_dict(self.details),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[TransactionPending], d: t.Dict[str, t.Any]
    ) -> TransactionPending:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tag=parsed.tag,
            details=parsed.details,
        )
        res.raw_data = d
        return res
