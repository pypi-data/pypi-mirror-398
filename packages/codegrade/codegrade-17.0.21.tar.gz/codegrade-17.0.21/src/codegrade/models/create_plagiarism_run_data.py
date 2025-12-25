"""The module that defines the ``CreatePlagiarismRunData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class CreatePlagiarismRunData:
    """The JSON to create a new plagiarism run."""

    #: The name of the plagiarism provider. Currently we only have JPlag.
    provider: str
    #: The list of the ids of the old assignments you want to include.
    old_assignments: t.Sequence[int]
    #: Any options specific for the provider.
    provider_options: t.Mapping[str, t.Any]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "provider",
                rqa.SimpleValue.str,
                doc="The name of the plagiarism provider. Currently we only have JPlag.",
            ),
            rqa.RequiredArgument(
                "old_assignments",
                rqa.List(rqa.SimpleValue.int),
                doc="The list of the ids of the old assignments you want to include.",
            ),
            rqa.RequiredArgument(
                "provider_options",
                rqa.LookupMapping(rqa.AnyValue),
                doc="Any options specific for the provider.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "provider": to_dict(self.provider),
            "old_assignments": to_dict(self.old_assignments),
            "provider_options": to_dict(self.provider_options),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CreatePlagiarismRunData], d: t.Dict[str, t.Any]
    ) -> CreatePlagiarismRunData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            provider=parsed.provider,
            old_assignments=parsed.old_assignments,
            provider_options=parsed.provider_options,
        )
        res.raw_data = d
        return res
