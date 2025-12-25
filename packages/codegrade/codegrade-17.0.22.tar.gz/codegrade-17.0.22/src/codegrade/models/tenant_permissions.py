"""The module that defines the ``TenantPermissions`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .global_perm_map import GlobalPermMap


@dataclass
class TenantPermissions:
    """The permissions of a user within a tenant."""

    #: Whether the user has permissions within this tenant.
    has_perms: t.Literal[True]
    #: The permissions of the user within this tenant.
    perms: GlobalPermMap

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "has_perms",
                rqa.LiteralBoolean(True),
                doc="Whether the user has permissions within this tenant.",
            ),
            rqa.RequiredArgument(
                "perms",
                parsers.ParserFor.make(GlobalPermMap),
                doc="The permissions of the user within this tenant.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "has_perms": to_dict(self.has_perms),
            "perms": to_dict(self.perms),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[TenantPermissions], d: t.Dict[str, t.Any]
    ) -> TenantPermissions:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            has_perms=parsed.has_perms,
            perms=parsed.perms,
        )
        res.raw_data = d
        return res
