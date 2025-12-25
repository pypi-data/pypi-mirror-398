"""The module that defines the ``LoginData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class LoginData:
    """The data required when you want to login"""

    #: The username of the user.
    username: str
    #: The id of the tenant of the user.
    tenant_id: str
    #: Your password
    password: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
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
            rqa.RequiredArgument(
                "password",
                rqa.SimpleValue.str,
                doc="Your password",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "username": to_dict(self.username),
            "tenant_id": to_dict(self.tenant_id),
            "password": to_dict(self.password),
        }
        return res

    @classmethod
    def from_dict(cls: t.Type[LoginData], d: t.Dict[str, t.Any]) -> LoginData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            username=parsed.username,
            tenant_id=parsed.tenant_id,
            password=parsed.password,
        )
        res.raw_data = d
        return res
