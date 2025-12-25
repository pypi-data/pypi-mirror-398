"""The module that defines the ``BaseUser`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class BaseUser:
    """The JSON representation of a user."""

    #: The is the id of this user
    id: int
    #: The username of this user.
    username: str
    #: The tenant of the user
    tenant_id: t.Optional[str]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "id",
                rqa.SimpleValue.int,
                doc="The is the id of this user",
            ),
            rqa.RequiredArgument(
                "username",
                rqa.SimpleValue.str,
                doc="The username of this user.",
            ),
            rqa.RequiredArgument(
                "tenant_id",
                rqa.Nullable(rqa.SimpleValue.str),
                doc="The tenant of the user",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "username": to_dict(self.username),
            "tenant_id": to_dict(self.tenant_id),
        }
        return res

    @classmethod
    def from_dict(cls: t.Type[BaseUser], d: t.Dict[str, t.Any]) -> BaseUser:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            username=parsed.username,
            tenant_id=parsed.tenant_id,
        )
        res.raw_data = d
        return res
