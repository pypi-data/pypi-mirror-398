"""The module that defines the ``AssignmentRestriction`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .assignment_restriction_not_set_password import (
    AssignmentRestrictionNotSetPassword,
)
from .assignment_restriction_set_password import (
    AssignmentRestrictionSetPassword,
)


@dataclass
class AssignmentRestriction:
    """The restrictions for the assignment."""

    #: Whether the assignment is password restricted or not.
    password: t.Union[
        AssignmentRestrictionSetPassword, AssignmentRestrictionNotSetPassword
    ]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "password",
                parsers.make_union(
                    parsers.ParserFor.make(AssignmentRestrictionSetPassword),
                    parsers.ParserFor.make(
                        AssignmentRestrictionNotSetPassword
                    ),
                ),
                doc="Whether the assignment is password restricted or not.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "password": to_dict(self.password),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AssignmentRestriction], d: t.Dict[str, t.Any]
    ) -> AssignmentRestriction:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            password=parsed.password,
        )
        res.raw_data = d
        return res
