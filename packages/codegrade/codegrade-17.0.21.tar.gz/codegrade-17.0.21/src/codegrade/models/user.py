"""The module that defines the ``User`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..parsers import ParserFor, make_union
from ..utils import to_dict
from .group_user import GroupUser
from .normal_user import NormalUser

User = t.Union[
    NormalUser,
    GroupUser,
]
UserParser = rqa.Lazy(
    lambda: make_union(ParserFor.make(NormalUser), ParserFor.make(GroupUser)),
)
