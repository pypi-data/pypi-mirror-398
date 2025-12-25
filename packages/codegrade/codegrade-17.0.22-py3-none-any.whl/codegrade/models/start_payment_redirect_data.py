"""The module that defines the ``StartPaymentRedirectData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class StartPaymentRedirectData:
    """Data to redirect after payment."""

    #: The action to perform after payment.
    mode: t.Literal["redirect"]
    #: We should redirect the user after the payment has completed
    next_route: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "mode",
                rqa.StringEnum("redirect"),
                doc="The action to perform after payment.",
            ),
            rqa.RequiredArgument(
                "next_route",
                rqa.SimpleValue.str,
                doc="We should redirect the user after the payment has completed",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "mode": to_dict(self.mode),
            "next_route": to_dict(self.next_route),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[StartPaymentRedirectData], d: t.Dict[str, t.Any]
    ) -> StartPaymentRedirectData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            mode=parsed.mode,
            next_route=parsed.next_route,
        )
        res.raw_data = d
        return res
