"""The module that defines the ``AccessExpired`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .payment_options import PaymentOptions


@dataclass
class AccessExpired:
    """State when a previous entitlement has expired."""

    #: The top-level status tag.
    tag: t.Literal["access-expired"]
    #: The moment the purchase was successful.
    success_at: datetime.datetime
    #: The timestamp when the access expired.
    expired_at: datetime.datetime
    #: The ways a user can pay to regain access.
    payment_options: PaymentOptions

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "tag",
                rqa.StringEnum("access-expired"),
                doc="The top-level status tag.",
            ),
            rqa.RequiredArgument(
                "success_at",
                rqa.RichValue.DateTime,
                doc="The moment the purchase was successful.",
            ),
            rqa.RequiredArgument(
                "expired_at",
                rqa.RichValue.DateTime,
                doc="The timestamp when the access expired.",
            ),
            rqa.RequiredArgument(
                "payment_options",
                parsers.ParserFor.make(PaymentOptions),
                doc="The ways a user can pay to regain access.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tag": to_dict(self.tag),
            "success_at": to_dict(self.success_at),
            "expired_at": to_dict(self.expired_at),
            "payment_options": to_dict(self.payment_options),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AccessExpired], d: t.Dict[str, t.Any]
    ) -> AccessExpired:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tag=parsed.tag,
            success_at=parsed.success_at,
            expired_at=parsed.expired_at,
            payment_options=parsed.payment_options,
        )
        res.raw_data = d
        return res
