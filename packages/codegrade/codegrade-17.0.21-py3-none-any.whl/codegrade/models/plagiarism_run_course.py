"""The module that defines the ``PlagiarismRunCourse`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class PlagiarismRunCourse:
    """This object represents an course that is connected to a plagiarism run
    or case.
    """

    #: The id of the course
    id: int
    #: The name of the course.
    name: str
    #: Is this is a virtual course?
    virtual: bool
    #: The moment the course was created.
    created_at: datetime.datetime

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "id",
                rqa.SimpleValue.int,
                doc="The id of the course",
            ),
            rqa.RequiredArgument(
                "name",
                rqa.SimpleValue.str,
                doc="The name of the course.",
            ),
            rqa.RequiredArgument(
                "virtual",
                rqa.SimpleValue.bool,
                doc="Is this is a virtual course?",
            ),
            rqa.RequiredArgument(
                "created_at",
                rqa.RichValue.DateTime,
                doc="The moment the course was created.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "name": to_dict(self.name),
            "virtual": to_dict(self.virtual),
            "created_at": to_dict(self.created_at),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PlagiarismRunCourse], d: t.Dict[str, t.Any]
    ) -> PlagiarismRunCourse:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            name=parsed.name,
            virtual=parsed.virtual,
            created_at=parsed.created_at,
        )
        res.raw_data = d
        return res
