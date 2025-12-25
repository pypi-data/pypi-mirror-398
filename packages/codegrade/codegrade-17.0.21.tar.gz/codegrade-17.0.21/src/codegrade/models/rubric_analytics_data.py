"""The module that defines the ``RubricAnalyticsData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .rubric_analytics_data_row import RubricAnalyticsDataRow


@dataclass
class RubricAnalyticsData:
    """The analytics for rubrics."""

    #: This is rubric data.
    tag: t.Literal["rubric"]
    #: The analytics per row.
    rows: t.Sequence[RubricAnalyticsDataRow]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "tag",
                rqa.StringEnum("rubric"),
                doc="This is rubric data.",
            ),
            rqa.RequiredArgument(
                "rows",
                rqa.List(parsers.ParserFor.make(RubricAnalyticsDataRow)),
                doc="The analytics per row.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tag": to_dict(self.tag),
            "rows": to_dict(self.rows),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[RubricAnalyticsData], d: t.Dict[str, t.Any]
    ) -> RubricAnalyticsData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tag=parsed.tag,
            rows=parsed.rows,
        )
        res.raw_data = d
        return res
