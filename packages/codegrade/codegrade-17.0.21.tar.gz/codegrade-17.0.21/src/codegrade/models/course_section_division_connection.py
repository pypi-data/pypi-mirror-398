"""The module that defines the ``CourseSectionDivisionConnection`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class CourseSectionDivisionConnection:
    """JSON representation of a course section division connection."""

    #: The id of this connection.
    id: str
    #: The username of the connected user.
    username: str
    #: The full name of the connected user.
    name: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "id",
                rqa.SimpleValue.str,
                doc="The id of this connection.",
            ),
            rqa.RequiredArgument(
                "username",
                rqa.SimpleValue.str,
                doc="The username of the connected user.",
            ),
            rqa.RequiredArgument(
                "name",
                rqa.SimpleValue.str,
                doc="The full name of the connected user.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "username": to_dict(self.username),
            "name": to_dict(self.name),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CourseSectionDivisionConnection], d: t.Dict[str, t.Any]
    ) -> CourseSectionDivisionConnection:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            username=parsed.username,
            name=parsed.name,
        )
        res.raw_data = d
        return res
