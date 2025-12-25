"""The module that defines the ``LaunchSecondPhaseLTIData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class LaunchSecondPhaseLTIData:
    """Input data required for the `LTI::LaunchSecondPhase` operation."""

    #: The identifier for the first phase blob data.
    blob_id: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "blob_id",
                rqa.SimpleValue.str,
                doc="The identifier for the first phase blob data.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "blob_id": to_dict(self.blob_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[LaunchSecondPhaseLTIData], d: t.Dict[str, t.Any]
    ) -> LaunchSecondPhaseLTIData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            blob_id=parsed.blob_id,
        )
        res.raw_data = d
        return res
