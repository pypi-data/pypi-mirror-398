"""The module that defines the ``AssignmentPeerFeedbackConnection`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .user import User, UserParser


@dataclass
class AssignmentPeerFeedbackConnection:
    """A peer feedback connection that connects two students."""

    subject: User
    peer: User

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "subject",
                UserParser,
                doc="",
            ),
            rqa.RequiredArgument(
                "peer",
                UserParser,
                doc="",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "subject": to_dict(self.subject),
            "peer": to_dict(self.peer),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AssignmentPeerFeedbackConnection], d: t.Dict[str, t.Any]
    ) -> AssignmentPeerFeedbackConnection:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            subject=parsed.subject,
            peer=parsed.peer,
        )
        res.raw_data = d
        return res
