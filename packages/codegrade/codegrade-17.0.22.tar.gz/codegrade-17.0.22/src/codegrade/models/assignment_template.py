"""The module that defines the ``AssignmentTemplate`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class AssignmentTemplate:
    """The JSON representation of an assignment template."""

    #: The id of the assignment of this template.
    assignment_id: int

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "assignment_id",
                rqa.SimpleValue.int,
                doc="The id of the assignment of this template.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "assignment_id": to_dict(self.assignment_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AssignmentTemplate], d: t.Dict[str, t.Any]
    ) -> AssignmentTemplate:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            assignment_id=parsed.assignment_id,
        )
        res.raw_data = d
        return res
