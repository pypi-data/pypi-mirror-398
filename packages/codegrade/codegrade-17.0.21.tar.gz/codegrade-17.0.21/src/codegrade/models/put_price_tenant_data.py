"""The module that defines the ``PutPriceTenantData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..parsers import ParserFor, make_union
from ..utils import to_dict
from .put_per_course_price_tenant_data import PutPerCoursePriceTenantData
from .put_tenant_wide_price_tenant_data import PutTenantWidePriceTenantData

PutPriceTenantData = t.Union[
    PutPerCoursePriceTenantData,
    PutTenantWidePriceTenantData,
]
PutPriceTenantDataParser = rqa.Lazy(
    lambda: make_union(
        ParserFor.make(PutPerCoursePriceTenantData),
        ParserFor.make(PutTenantWidePriceTenantData),
    ),
)
