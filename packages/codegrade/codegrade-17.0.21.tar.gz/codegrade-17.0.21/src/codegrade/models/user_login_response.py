"""The module that defines the ``UserLoginResponse`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .extended_user import ExtendedUser
from .session_restriction_data import SessionRestrictionData


@dataclass
class UserLoginResponse:
    """When logging in this object will be given."""

    #: The user that was logged in.
    user: ExtendedUser
    #: A session token that can be used to do authenticated requests.
    access_token: str
    #: The restrictions of this access token.
    restrictions: SessionRestrictionData
    #: When this token expires.
    expires_at: datetime.datetime

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "user",
                parsers.ParserFor.make(ExtendedUser),
                doc="The user that was logged in.",
            ),
            rqa.RequiredArgument(
                "access_token",
                rqa.SimpleValue.str,
                doc="A session token that can be used to do authenticated requests.",
            ),
            rqa.RequiredArgument(
                "restrictions",
                parsers.ParserFor.make(SessionRestrictionData),
                doc="The restrictions of this access token.",
            ),
            rqa.RequiredArgument(
                "expires_at",
                rqa.RichValue.DateTime,
                doc="When this token expires.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "user": to_dict(self.user),
            "access_token": to_dict(self.access_token),
            "restrictions": to_dict(self.restrictions),
            "expires_at": to_dict(self.expires_at),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[UserLoginResponse], d: t.Dict[str, t.Any]
    ) -> UserLoginResponse:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            user=parsed.user,
            access_token=parsed.access_token,
            restrictions=parsed.restrictions,
            expires_at=parsed.expires_at,
        )
        res.raw_data = d
        return res
