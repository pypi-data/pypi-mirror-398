"""The module that defines the ``AnalyticsData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .inline_feedback_analytics_data import InlineFeedbackAnalyticsData
from .rubric_analytics_data import RubricAnalyticsData
from .submissions_analytics_data import SubmissionsAnalyticsData


@dataclass
class AnalyticsData:
    """The analytics data."""

    #: The id of the work this metric is for.
    work_id: int
    #: The data of the metric.
    data: t.Union[
        SubmissionsAnalyticsData,
        RubricAnalyticsData,
        InlineFeedbackAnalyticsData,
    ]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "work_id",
                rqa.SimpleValue.int,
                doc="The id of the work this metric is for.",
            ),
            rqa.RequiredArgument(
                "data",
                parsers.make_union(
                    parsers.ParserFor.make(SubmissionsAnalyticsData),
                    parsers.ParserFor.make(RubricAnalyticsData),
                    parsers.ParserFor.make(InlineFeedbackAnalyticsData),
                ),
                doc="The data of the metric.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "work_id": to_dict(self.work_id),
            "data": to_dict(self.data),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AnalyticsData], d: t.Dict[str, t.Any]
    ) -> AnalyticsData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            work_id=parsed.work_id,
            data=parsed.data,
        )
        res.raw_data = d
        return res
