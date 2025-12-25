"""The module that defines the ``PatchProviderLTIData`` model.

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
class PatchProviderLTIData:
    """Input data required for the `LTI::PatchProvider` operation."""

    #: New label for the provider.
    label: Maybe[str] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.OptionalArgument(
                "label",
                rqa.SimpleValue.str,
                doc="New label for the provider.",
            ),
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.label = maybe_from_nullable(self.label)

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {}
        if self.label.is_just:
            res["label"] = to_dict(self.label.value)
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PatchProviderLTIData], d: t.Dict[str, t.Any]
    ) -> PatchProviderLTIData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            label=parsed.label,
        )
        res.raw_data = d
        return res
