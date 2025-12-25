"""The module that defines the ``RoleAsJSONWithPerms`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .abstract_role import AbstractRole
from .global_perm_map import GlobalPermMap


@dataclass
class RoleAsJSONWithPerms(AbstractRole):
    """This role with the permissions the role has."""

    #: The permissions this role has
    perms: GlobalPermMap
    #: Does the currently logged in user have this role.
    own: bool
    #: The number of users with this role.
    count: int

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: AbstractRole.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "perms",
                    parsers.ParserFor.make(GlobalPermMap),
                    doc="The permissions this role has",
                ),
                rqa.RequiredArgument(
                    "own",
                    rqa.SimpleValue.bool,
                    doc="Does the currently logged in user have this role.",
                ),
                rqa.RequiredArgument(
                    "count",
                    rqa.SimpleValue.int,
                    doc="The number of users with this role.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "perms": to_dict(self.perms),
            "own": to_dict(self.own),
            "count": to_dict(self.count),
            "id": to_dict(self.id),
            "name": to_dict(self.name),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[RoleAsJSONWithPerms], d: t.Dict[str, t.Any]
    ) -> RoleAsJSONWithPerms:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            perms=parsed.perms,
            own=parsed.own,
            count=parsed.count,
            id=parsed.id,
            name=parsed.name,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    pass
