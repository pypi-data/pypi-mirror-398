"""The module that defines the ``PlagiarismCaseSubmission`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .user import User, UserParser


@dataclass
class PlagiarismCaseSubmission:
    """This object represents an assignment that is connected to a plagiarism
    run or case.
    """

    #: The id of the submission.
    id: int
    #: The id of the assignment of the submission.
    assignment_id: int
    user: User
    #: The moment the submission was created.
    created_at: datetime.datetime

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "id",
                rqa.SimpleValue.int,
                doc="The id of the submission.",
            ),
            rqa.RequiredArgument(
                "assignment_id",
                rqa.SimpleValue.int,
                doc="The id of the assignment of the submission.",
            ),
            rqa.RequiredArgument(
                "user",
                UserParser,
                doc="",
            ),
            rqa.RequiredArgument(
                "created_at",
                rqa.RichValue.DateTime,
                doc="The moment the submission was created.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "assignment_id": to_dict(self.assignment_id),
            "user": to_dict(self.user),
            "created_at": to_dict(self.created_at),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PlagiarismCaseSubmission], d: t.Dict[str, t.Any]
    ) -> PlagiarismCaseSubmission:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            assignment_id=parsed.assignment_id,
            user=parsed.user,
            created_at=parsed.created_at,
        )
        res.raw_data = d
        return res
