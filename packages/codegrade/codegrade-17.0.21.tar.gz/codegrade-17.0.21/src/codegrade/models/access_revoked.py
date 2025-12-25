"""The module that defines the ``AccessRevoked`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .payment_options import PaymentOptions


@dataclass
class AccessRevoked:
    """State when access has been removed, allowing users to pay again."""

    #: The top-level status tag.
    tag: t.Literal["access-revoked"]
    #: The ways a user can pay to regain access.
    payment_options: PaymentOptions

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "tag",
                rqa.StringEnum("access-revoked"),
                doc="The top-level status tag.",
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
            "payment_options": to_dict(self.payment_options),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AccessRevoked], d: t.Dict[str, t.Any]
    ) -> AccessRevoked:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tag=parsed.tag,
            payment_options=parsed.payment_options,
        )
        res.raw_data = d
        return res
