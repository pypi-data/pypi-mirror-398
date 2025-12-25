"""The module that defines the ``UserInfoWithRole`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class UserInfoWithRole:
    """The personal information of a user and their role."""

    #: The id of the role of this user.
    role_id: int
    #: The username for logging in of the user.
    username: str
    #: The full name of the user.
    name: str
    #: The email address of the user.
    email: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "role_id",
                rqa.SimpleValue.int,
                doc="The id of the role of this user.",
            ),
            rqa.RequiredArgument(
                "username",
                rqa.SimpleValue.str,
                doc="The username for logging in of the user.",
            ),
            rqa.RequiredArgument(
                "name",
                rqa.SimpleValue.str,
                doc="The full name of the user.",
            ),
            rqa.RequiredArgument(
                "email",
                rqa.SimpleValue.str,
                doc="The email address of the user.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "role_id": to_dict(self.role_id),
            "username": to_dict(self.username),
            "name": to_dict(self.name),
            "email": to_dict(self.email),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[UserInfoWithRole], d: t.Dict[str, t.Any]
    ) -> UserInfoWithRole:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            role_id=parsed.role_id,
            username=parsed.username,
            name=parsed.name,
            email=parsed.email,
        )
        res.raw_data = d
        return res
