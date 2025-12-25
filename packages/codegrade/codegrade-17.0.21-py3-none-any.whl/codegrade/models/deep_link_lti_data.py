"""The module that defines the ``DeepLinkLTIData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from ..utils import to_dict


@dataclass
class DeepLinkLTIData:
    """Input data required for the `LTI::DeepLink` operation."""

    #: The authentication token received after the initial LTI launch.
    auth_token: str
    #: The name of the new assignment
    name: str
    #: The deadline of the new assignment, formatted as an ISO8601 datetime
    #: string.
    deadline: datetime.datetime
    #: The lock date of the new assignment, formatted as an ISO8601 datetime
    #: string.
    lock_date: Maybe[t.Optional[datetime.datetime]] = Nothing
    #: The available at of the new assignment, formatted as an ISO8601 datetime
    #: string.
    available_at: Maybe[t.Optional[datetime.datetime]] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "auth_token",
                rqa.SimpleValue.str,
                doc="The authentication token received after the initial LTI launch.",
            ),
            rqa.RequiredArgument(
                "name",
                rqa.SimpleValue.str,
                doc="The name of the new assignment",
            ),
            rqa.RequiredArgument(
                "deadline",
                rqa.RichValue.DateTime,
                doc="The deadline of the new assignment, formatted as an ISO8601 datetime string.",
            ),
            rqa.OptionalArgument(
                "lock_date",
                rqa.Nullable(rqa.RichValue.DateTime),
                doc="The lock date of the new assignment, formatted as an ISO8601 datetime string.",
            ),
            rqa.OptionalArgument(
                "available_at",
                rqa.Nullable(rqa.RichValue.DateTime),
                doc="The available at of the new assignment, formatted as an ISO8601 datetime string.",
            ),
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.lock_date = maybe_from_nullable(self.lock_date)
        self.available_at = maybe_from_nullable(self.available_at)

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "auth_token": to_dict(self.auth_token),
            "name": to_dict(self.name),
            "deadline": to_dict(self.deadline),
        }
        if self.lock_date.is_just:
            res["lock_date"] = to_dict(self.lock_date.value)
        if self.available_at.is_just:
            res["available_at"] = to_dict(self.available_at.value)
        return res

    @classmethod
    def from_dict(
        cls: t.Type[DeepLinkLTIData], d: t.Dict[str, t.Any]
    ) -> DeepLinkLTIData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            auth_token=parsed.auth_token,
            name=parsed.name,
            deadline=parsed.deadline,
            lock_date=parsed.lock_date,
            available_at=parsed.available_at,
        )
        res.raw_data = d
        return res
