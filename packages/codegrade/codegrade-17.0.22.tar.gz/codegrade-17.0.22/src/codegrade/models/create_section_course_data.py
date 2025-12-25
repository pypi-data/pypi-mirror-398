"""The module that defines the ``CreateSectionCourseData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class CreateSectionCourseData:
    """Input data required for the `Course::CreateSection` operation."""

    #: The name of the new section.
    name: str
    #: The ids of the users that will be added to the new section.
    user_ids: t.Sequence[int]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "name",
                rqa.SimpleValue.str,
                doc="The name of the new section.",
            ),
            rqa.RequiredArgument(
                "user_ids",
                rqa.List(rqa.SimpleValue.int),
                doc="The ids of the users that will be added to the new section.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "name": to_dict(self.name),
            "user_ids": to_dict(self.user_ids),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CreateSectionCourseData], d: t.Dict[str, t.Any]
    ) -> CreateSectionCourseData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            name=parsed.name,
            user_ids=parsed.user_ids,
        )
        res.raw_data = d
        return res
