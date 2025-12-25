"""The module that defines the ``ExtendedAutoTestRun`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .auto_test_result import AutoTestResult
from .auto_test_run import AutoTestRun


@dataclass
class ExtendedAutoTestRun(AutoTestRun):
    """The run as extended JSON."""

    #: The results in this run. This will only contain the result for the
    #: latest submissions.
    results: t.Sequence[AutoTestResult]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: AutoTestRun.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "results",
                    rqa.List(parsers.ParserFor.make(AutoTestResult)),
                    doc="The results in this run. This will only contain the result for the latest submissions.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "results": to_dict(self.results),
            "id": to_dict(self.id),
            "created_at": to_dict(self.created_at),
            "state": to_dict(self.state),
            "is_continuous": to_dict(self.is_continuous),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[ExtendedAutoTestRun], d: t.Dict[str, t.Any]
    ) -> ExtendedAutoTestRun:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            results=parsed.results,
            id=parsed.id,
            created_at=parsed.created_at,
            state=parsed.state,
            is_continuous=parsed.is_continuous,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime
