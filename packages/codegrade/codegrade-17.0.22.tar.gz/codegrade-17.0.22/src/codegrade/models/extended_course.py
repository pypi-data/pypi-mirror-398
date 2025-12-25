"""The module that defines the ``ExtendedCourse`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .course import Course
from .finalized_lti1p1_provider import FinalizedLTI1p1Provider
from .finalized_lti1p3_provider import FinalizedLTI1p3Provider
from .non_finalized_lti1p1_provider import NonFinalizedLTI1p1Provider
from .non_finalized_lti1p3_provider import NonFinalizedLTI1p3Provider


@dataclass
class ExtendedCourse(Course):
    """The way this class will be represented in extended JSON."""

    #: The lti provider that manages this course, if `null` this is not a LTI
    #: course.
    lti_provider: t.Optional[
        t.Union[
            NonFinalizedLTI1p3Provider,
            NonFinalizedLTI1p1Provider,
            FinalizedLTI1p3Provider,
            FinalizedLTI1p1Provider,
        ]
    ]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: Course.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "lti_provider",
                    rqa.Nullable(
                        parsers.make_union(
                            parsers.ParserFor.make(NonFinalizedLTI1p3Provider),
                            parsers.ParserFor.make(NonFinalizedLTI1p1Provider),
                            parsers.ParserFor.make(FinalizedLTI1p3Provider),
                            parsers.ParserFor.make(FinalizedLTI1p1Provider),
                        )
                    ),
                    doc="The lti provider that manages this course, if `null` this is not a LTI course.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "lti_provider": to_dict(self.lti_provider),
            "id": to_dict(self.id),
            "name": to_dict(self.name),
            "created_at": to_dict(self.created_at),
            "virtual": to_dict(self.virtual),
            "state": to_dict(self.state),
            "tenant_id": to_dict(self.tenant_id),
            "price": to_dict(self.price),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[ExtendedCourse], d: t.Dict[str, t.Any]
    ) -> ExtendedCourse:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            lti_provider=parsed.lti_provider,
            id=parsed.id,
            name=parsed.name,
            created_at=parsed.created_at,
            virtual=parsed.virtual,
            state=parsed.state,
            tenant_id=parsed.tenant_id,
            price=parsed.price,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    import datetime

    from .course_price import CoursePrice
    from .course_state import CourseState
