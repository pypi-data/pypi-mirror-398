"""The module that defines the ``BaseLaunchData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .extended_course import ExtendedCourse
from .user_login_response import UserLoginResponse


@dataclass
class BaseLaunchData:
    """The base data for LTI launches."""

    #: The course of the LTI launch. This is always included, even if the
    #: course already did exist.
    course: ExtendedCourse
    #: If a new role needed to be created to give the current user a role the
    #: name of the new role will be stored in this variable. If no role was
    #: created it the value is `None`.
    new_role_created: t.Optional[str]
    #: If the current user needs a new session to login it will be stored here,
    #: otherwise `None`.
    new_session: t.Optional[UserLoginResponse]
    #: If the email of the user was updated by this LTI launch the new email
    #: will be given, if no email was updated it will be `None`.
    updated_email: t.Optional[str]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "course",
                parsers.ParserFor.make(ExtendedCourse),
                doc="The course of the LTI launch. This is always included, even if the course already did exist.",
            ),
            rqa.RequiredArgument(
                "new_role_created",
                rqa.Nullable(rqa.SimpleValue.str),
                doc="If a new role needed to be created to give the current user a role the name of the new role will be stored in this variable. If no role was created it the value is `None`.",
            ),
            rqa.RequiredArgument(
                "new_session",
                rqa.Nullable(parsers.ParserFor.make(UserLoginResponse)),
                doc="If the current user needs a new session to login it will be stored here, otherwise `None`.",
            ),
            rqa.RequiredArgument(
                "updated_email",
                rqa.Nullable(rqa.SimpleValue.str),
                doc="If the email of the user was updated by this LTI launch the new email will be given, if no email was updated it will be `None`.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "course": to_dict(self.course),
            "new_role_created": to_dict(self.new_role_created),
            "new_session": to_dict(self.new_session),
            "updated_email": to_dict(self.updated_email),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[BaseLaunchData], d: t.Dict[str, t.Any]
    ) -> BaseLaunchData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            course=parsed.course,
            new_role_created=parsed.new_role_created,
            new_session=parsed.new_session,
            updated_email=parsed.updated_email,
        )
        res.raw_data = d
        return res
