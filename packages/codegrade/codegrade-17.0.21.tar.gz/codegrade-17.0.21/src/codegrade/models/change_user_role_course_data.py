"""The module that defines the ``ChangeUserRoleCourseData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..parsers import ParserFor, make_union
from ..utils import to_dict


@dataclass
class ChangeUserRoleCourseData_1:
    """Pass this data if you want to change the role of an existing member."""

    #: The id of the new role the user.
    role_id: int
    #: The id of the user of which you want to change the role.
    user_id: int

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "role_id",
                rqa.SimpleValue.int,
                doc="The id of the new role the user.",
            ),
            rqa.RequiredArgument(
                "user_id",
                rqa.SimpleValue.int,
                doc="The id of the user of which you want to change the role.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "role_id": to_dict(self.role_id),
            "user_id": to_dict(self.user_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[ChangeUserRoleCourseData_1], d: t.Dict[str, t.Any]
    ) -> ChangeUserRoleCourseData_1:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            role_id=parsed.role_id,
            user_id=parsed.user_id,
        )
        res.raw_data = d
        return res


@dataclass
class ChangeUserRoleCourseData_1_2:
    """Pass this data if you want to enroll a new user"""

    #: The id of the new role the user.
    role_id: int
    #: The username of the user.
    username: str
    #: The id of the tenant of the user.
    tenant_id: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "role_id",
                rqa.SimpleValue.int,
                doc="The id of the new role the user.",
            ),
            rqa.RequiredArgument(
                "username",
                rqa.SimpleValue.str,
                doc="The username of the user.",
            ),
            rqa.RequiredArgument(
                "tenant_id",
                rqa.SimpleValue.str,
                doc="The id of the tenant of the user.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "role_id": to_dict(self.role_id),
            "username": to_dict(self.username),
            "tenant_id": to_dict(self.tenant_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[ChangeUserRoleCourseData_1_2], d: t.Dict[str, t.Any]
    ) -> ChangeUserRoleCourseData_1_2:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            role_id=parsed.role_id,
            username=parsed.username,
            tenant_id=parsed.tenant_id,
        )
        res.raw_data = d
        return res


ChangeUserRoleCourseData = t.Union[
    ChangeUserRoleCourseData_1,
    ChangeUserRoleCourseData_1_2,
]
ChangeUserRoleCourseDataParser = rqa.Lazy(
    lambda: make_union(
        ParserFor.make(ChangeUserRoleCourseData_1),
        ParserFor.make(ChangeUserRoleCourseData_1_2),
    ),
)
