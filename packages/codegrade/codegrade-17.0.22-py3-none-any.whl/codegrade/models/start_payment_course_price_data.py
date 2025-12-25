"""The module that defines the ``StartPaymentCoursePriceData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..parsers import ParserFor, make_union
from ..utils import to_dict
from .start_payment_close_tab_data import StartPaymentCloseTabData
from .start_payment_redirect_data import StartPaymentRedirectData

StartPaymentCoursePriceData = t.Union[
    StartPaymentCloseTabData,
    StartPaymentRedirectData,
]
StartPaymentCoursePriceDataParser = rqa.Lazy(
    lambda: make_union(
        ParserFor.make(StartPaymentCloseTabData),
        ParserFor.make(StartPaymentRedirectData),
    ),
)
