"""The module that defines the ``NormalUser`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict
from .base_user import BaseUser


@dataclass
class NormalUser(BaseUser):
    """This is a normal user, not a virtual wrapper for a group."""

    #: The tag of this class.
    type: t.Literal["normal"]
    #: The fullname of the user. This might contain a first and last name,
    #: however this is not guaranteed. This might be None if the PII for this
    #: user cannot be retrieved anymore.
    name: t.Optional[str]
    #: Is this user a test student.
    is_test_student: bool

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseUser.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "type",
                    rqa.StringEnum("normal"),
                    doc="The tag of this class.",
                ),
                rqa.RequiredArgument(
                    "name",
                    rqa.Nullable(rqa.SimpleValue.str),
                    doc="The fullname of the user. This might contain a first and last name, however this is not guaranteed. This might be None if the PII for this user cannot be retrieved anymore.",
                ),
                rqa.RequiredArgument(
                    "is_test_student",
                    rqa.SimpleValue.bool,
                    doc="Is this user a test student.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
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
        cls: t.Type[NormalUser], d: t.Dict[str, t.Any]
    ) -> NormalUser:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
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
    pass
