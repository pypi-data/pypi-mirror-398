"""The module that defines the ``PutDivisionParentAssignmentData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class PutDivisionParentAssignmentData:
    """Input data required for the `Assignment::PutDivisionParent` operation."""

    #: The id of the new division parent of this assignment.
    parent_id: t.Optional[int]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "parent_id",
                rqa.Nullable(rqa.SimpleValue.int),
                doc="The id of the new division parent of this assignment.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "parent_id": to_dict(self.parent_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PutDivisionParentAssignmentData], d: t.Dict[str, t.Any]
    ) -> PutDivisionParentAssignmentData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            parent_id=parsed.parent_id,
        )
        res.raw_data = d
        return res
