"""The module that defines the ``PearsonTemplate`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class PearsonTemplate:
    """A Pearson template from an LTI launch."""

    #: The type of the dict.
    type: t.Literal["pearson-template"]
    #: The id of the template.
    id: str
    #: If the template is still editable.
    editable: bool

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "type",
                rqa.StringEnum("pearson-template"),
                doc="The type of the dict.",
            ),
            rqa.RequiredArgument(
                "id",
                rqa.SimpleValue.str,
                doc="The id of the template.",
            ),
            rqa.RequiredArgument(
                "editable",
                rqa.SimpleValue.bool,
                doc="If the template is still editable.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "type": to_dict(self.type),
            "id": to_dict(self.id),
            "editable": to_dict(self.editable),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PearsonTemplate], d: t.Dict[str, t.Any]
    ) -> PearsonTemplate:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            type=parsed.type,
            id=parsed.id,
            editable=parsed.editable,
        )
        res.raw_data = d
        return res
