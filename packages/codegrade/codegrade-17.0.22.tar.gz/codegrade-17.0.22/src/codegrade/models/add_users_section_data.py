"""The module that defines the ``AddUsersSectionData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class AddUsersSectionData:
    """Input data required for the `Section::AddUsers` operation."""

    #: The ids of the users to add to this course section.
    user_ids: t.Sequence[int]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "user_ids",
                rqa.List(rqa.SimpleValue.int),
                doc="The ids of the users to add to this course section.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "user_ids": to_dict(self.user_ids),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AddUsersSectionData], d: t.Dict[str, t.Any]
    ) -> AddUsersSectionData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            user_ids=parsed.user_ids,
        )
        res.raw_data = d
        return res
