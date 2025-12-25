"""The module that defines the ``GroupUser`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .base_user import BaseUser
from .group import Group


@dataclass
class GroupUser(BaseUser):
    """This is a user that wraps a group."""

    #: The tag of this class.
    type: t.Literal["group-user"]
    #: The group that this user wraps.
    group: Group
    #: This user is never a test student.
    is_test_student: t.Literal[False]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseUser.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "type",
                    rqa.StringEnum("group-user"),
                    doc="The tag of this class.",
                ),
                rqa.RequiredArgument(
                    "group",
                    parsers.ParserFor.make(Group),
                    doc="The group that this user wraps.",
                ),
                rqa.RequiredArgument(
                    "is_test_student",
                    rqa.LiteralBoolean(False),
                    doc="This user is never a test student.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "type": to_dict(self.type),
            "group": to_dict(self.group),
            "is_test_student": to_dict(self.is_test_student),
            "id": to_dict(self.id),
            "username": to_dict(self.username),
            "tenant_id": to_dict(self.tenant_id),
        }
        return res

    @classmethod
    def from_dict(cls: t.Type[GroupUser], d: t.Dict[str, t.Any]) -> GroupUser:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            type=parsed.type,
            group=parsed.group,
            is_test_student=parsed.is_test_student,
            id=parsed.id,
            username=parsed.username,
            tenant_id=parsed.tenant_id,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    pass
