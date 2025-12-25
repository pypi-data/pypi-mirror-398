"""The module that defines the ``AccessGranted`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .coupon_grant import CouponGrant
from .purchase_grant import PurchaseGrant


@dataclass
class AccessGranted:
    """State when the user has active access via a specific entitlement."""

    #: The top-level status tag.
    tag: t.Literal["access-granted"]
    #: A discriminated union detailing how access was granted.
    grant: t.Union[PurchaseGrant, CouponGrant]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "tag",
                rqa.StringEnum("access-granted"),
                doc="The top-level status tag.",
            ),
            rqa.RequiredArgument(
                "grant",
                parsers.make_union(
                    parsers.ParserFor.make(PurchaseGrant),
                    parsers.ParserFor.make(CouponGrant),
                ),
                doc="A discriminated union detailing how access was granted.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tag": to_dict(self.tag),
            "grant": to_dict(self.grant),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AccessGranted], d: t.Dict[str, t.Any]
    ) -> AccessGranted:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tag=parsed.tag,
            grant=parsed.grant,
        )
        res.raw_data = d
        return res
