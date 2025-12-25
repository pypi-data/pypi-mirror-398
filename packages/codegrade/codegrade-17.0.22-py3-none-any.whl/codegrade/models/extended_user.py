"""The module that defines the ``ExtendedUser`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .global_perm_map import GlobalPermMap
from .normal_user import NormalUser


@dataclass
class ExtendedUser(NormalUser):
    """The extended JSON representation of a user."""

    #: The email of the user. This will only be provided for the currently
    #: logged in user.
    email: t.Optional[str]
    #: Can this user see hidden assignments at least in one course.
    hidden: bool
    #: The global permissions of the user.
    permissions: GlobalPermMap

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: NormalUser.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "email",
                    rqa.Nullable(rqa.SimpleValue.str),
                    doc="The email of the user. This will only be provided for the currently logged in user.",
                ),
                rqa.RequiredArgument(
                    "hidden",
                    rqa.SimpleValue.bool,
                    doc="Can this user see hidden assignments at least in one course.",
                ),
                rqa.RequiredArgument(
                    "permissions",
                    parsers.ParserFor.make(GlobalPermMap),
                    doc="The global permissions of the user.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "email": to_dict(self.email),
            "hidden": to_dict(self.hidden),
            "permissions": to_dict(self.permissions),
            "type": to_dict(self.type),
            "name": to_dict(self.name),
            "is_test_student": to_dict(self.is_test_student),
            "id": to_dict(self.id),
            "username": to_dict(self.username),
            "tenant_id": to_dict(self.tenant_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[ExtendedUser], d: t.Dict[str, t.Any]
    ) -> ExtendedUser:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            email=parsed.email,
            hidden=parsed.hidden,
            permissions=parsed.permissions,
            type=parsed.type,
            name=parsed.name,
            is_test_student=parsed.is_test_student,
            id=parsed.id,
            username=parsed.username,
            tenant_id=parsed.tenant_id,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    from .base_user import BaseUser
