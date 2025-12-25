"""The module that defines the ``PatchSectionData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from ..utils import to_dict


@dataclass
class PatchSectionData:
    """Input data required for the `Section::Patch` operation."""

    #: New name for the course section.
    name: Maybe[str] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.OptionalArgument(
                "name",
                rqa.SimpleValue.str,
                doc="New name for the course section.",
            ),
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.name = maybe_from_nullable(self.name)

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {}
        if self.name.is_just:
            res["name"] = to_dict(self.name.value)
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PatchSectionData], d: t.Dict[str, t.Any]
    ) -> PatchSectionData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            name=parsed.name,
        )
        res.raw_data = d
        return res
