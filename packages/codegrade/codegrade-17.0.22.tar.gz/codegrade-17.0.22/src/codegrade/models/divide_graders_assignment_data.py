"""The module that defines the ``DivideGradersAssignmentData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict


@dataclass
class DivideGradersAssignmentData:
    """Input data required for the `Assignment::DivideGraders` operation."""

    #: The id of the new division parent of this assignment.
    graders: t.Mapping[str, t.Union[int, float]]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "graders",
                rqa.LookupMapping(
                    parsers.make_union(
                        rqa.SimpleValue.int, rqa.SimpleValue.float
                    )
                ),
                doc="The id of the new division parent of this assignment.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "graders": to_dict(self.graders),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[DivideGradersAssignmentData], d: t.Dict[str, t.Any]
    ) -> DivideGradersAssignmentData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            graders=parsed.graders,
        )
        res.raw_data = d
        return res
