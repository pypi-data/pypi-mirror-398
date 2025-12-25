"""The module that defines the ``FixedGradeAvailability`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class FixedGradeAvailability:
    """The state of the grade availability is set to a fixed value."""

    #: The tag for this data.
    tag: t.Literal["fixed"]
    #: If the assignment grade is available or not.
    value: bool

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "tag",
                rqa.StringEnum("fixed"),
                doc="The tag for this data.",
            ),
            rqa.RequiredArgument(
                "value",
                rqa.SimpleValue.bool,
                doc="If the assignment grade is available or not.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tag": to_dict(self.tag),
            "value": to_dict(self.value),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[FixedGradeAvailability], d: t.Dict[str, t.Any]
    ) -> FixedGradeAvailability:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tag=parsed.tag,
            value=parsed.value,
        )
        res.raw_data = d
        return res
