"""The module that defines the ``CourseCouponUsage`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .base_coupon_usage import BaseCouponUsage
from .course_coupon import CourseCoupon, CourseCouponParser


@dataclass
class CourseCouponUsage(BaseCouponUsage):
    """A link that represents the usage of a coupon by a user."""

    #: Scope of the coupon usage.
    scope: t.Literal["course"]
    coupon: CourseCoupon

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseCouponUsage.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "scope",
                    rqa.StringEnum("course"),
                    doc="Scope of the coupon usage.",
                ),
                rqa.RequiredArgument(
                    "coupon",
                    CourseCouponParser,
                    doc="",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "scope": to_dict(self.scope),
            "coupon": to_dict(self.coupon),
            "id": to_dict(self.id),
            "success_at": to_dict(self.success_at),
            "user_id": to_dict(self.user_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CourseCouponUsage], d: t.Dict[str, t.Any]
    ) -> CourseCouponUsage:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            scope=parsed.scope,
            coupon=parsed.coupon,
            id=parsed.id,
            success_at=parsed.success_at,
            user_id=parsed.user_id,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime
