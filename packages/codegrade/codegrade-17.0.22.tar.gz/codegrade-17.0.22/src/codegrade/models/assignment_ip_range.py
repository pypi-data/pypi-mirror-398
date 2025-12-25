"""The module that defines the ``AssignmentIPRange`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class AssignmentIPRange:
    """The JSON representation of an AssignmentIPRange."""

    #: The IP range in CIDR format.
    ip_range: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "ip_range",
                rqa.SimpleValue.str,
                doc="The IP range in CIDR format.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "ip_range": to_dict(self.ip_range),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AssignmentIPRange], d: t.Dict[str, t.Any]
    ) -> AssignmentIPRange:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            ip_range=parsed.ip_range,
        )
        res.raw_data = d
        return res
