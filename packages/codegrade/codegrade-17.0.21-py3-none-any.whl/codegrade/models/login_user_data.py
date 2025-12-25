"""The module that defines the ``LoginUserData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..parsers import ParserFor, make_union
from ..utils import to_dict
from .impersonate_data import ImpersonateData
from .login_data import LoginData

LoginUserData = t.Union[
    LoginData,
    ImpersonateData,
]
LoginUserDataParser = rqa.Lazy(
    lambda: make_union(
        ParserFor.make(LoginData), ParserFor.make(ImpersonateData)
    ),
)
