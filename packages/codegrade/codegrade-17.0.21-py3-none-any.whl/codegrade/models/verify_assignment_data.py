"""The module that defines the ``VerifyAssignmentData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class VerifyAssignmentData:
    """Input data required for the `Assignment::Verify` operation."""

    #: The password to verify
    password: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "password",
                rqa.SimpleValue.str,
                doc="The password to verify",
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
        cls: t.Type[VerifyAssignmentData], d: t.Dict[str, t.Any]
    ) -> VerifyAssignmentData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            password=parsed.password,
        )
        res.raw_data = d
        return res
