"""The module that defines the ``AccessPassCoupon`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..parsers import ParserFor, make_union
from ..utils import to_dict
from .access_pass_coupon_with_code import AccessPassCouponWithCode
from .access_pass_coupon_without_code import AccessPassCouponWithoutCode

AccessPassCoupon = t.Union[
    AccessPassCouponWithCode,
    AccessPassCouponWithoutCode,
]
AccessPassCouponParser = rqa.Lazy(
    lambda: make_union(
        ParserFor.make(AccessPassCouponWithCode),
        ParserFor.make(AccessPassCouponWithoutCode),
    ),
)
