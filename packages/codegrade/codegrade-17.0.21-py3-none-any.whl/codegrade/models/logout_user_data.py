"""The module that defines the ``LogoutUserData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class LogoutUserData:
    """Input data required for the `User::Logout` operation."""

    #: The token you want to invalidate
    token: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "token",
                rqa.SimpleValue.str,
                doc="The token you want to invalidate",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "token": to_dict(self.token),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[LogoutUserData], d: t.Dict[str, t.Any]
    ) -> LogoutUserData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            token=parsed.token,
        )
        res.raw_data = d
        return res
