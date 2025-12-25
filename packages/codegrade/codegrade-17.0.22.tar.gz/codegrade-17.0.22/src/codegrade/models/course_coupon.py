"""The module that defines the ``CourseCoupon`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..parsers import ParserFor, make_union
from ..utils import to_dict
from .coupon_with_code import CouponWithCode
from .coupon_without_code import CouponWithoutCode

CourseCoupon = t.Union[
    CouponWithCode,
    CouponWithoutCode,
]
CourseCouponParser = rqa.Lazy(
    lambda: make_union(
        ParserFor.make(CouponWithCode), ParserFor.make(CouponWithoutCode)
    ),
)
