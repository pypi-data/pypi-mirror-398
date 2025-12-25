"""The module that defines the ``RemovedPermissions`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .course_permission import CoursePermission


@dataclass
class RemovedPermissions:
    """The removed permissions for this session."""

    #: The course permissions which are removed in this session. DO NOT assume
    #: that the user has these permissions normally.
    course: t.Sequence[CoursePermission]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "course",
                rqa.List(rqa.EnumValue(CoursePermission)),
                doc="The course permissions which are removed in this session. DO NOT assume that the user has these permissions normally.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "course": to_dict(self.course),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[RemovedPermissions], d: t.Dict[str, t.Any]
    ) -> RemovedPermissions:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            course=parsed.course,
        )
        res.raw_data = d
        return res
