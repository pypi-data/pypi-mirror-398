"""The module that defines the ``SessionRestrictionData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from .. import parsers
from ..utils import to_dict
from .removed_permissions import RemovedPermissions
from .session_restriction_context import SessionRestrictionContext


@dataclass
class SessionRestrictionData:
    """Restrictions of the session."""

    #: If set and not none this is the course for which the token is valid.
    for_context: Maybe[SessionRestrictionContext] = Nothing
    #: The removed permissions for a session.
    removed_permissions: Maybe[RemovedPermissions] = Nothing
    #: Assignments with password access restriction.
    verified_assignment_ids: Maybe[t.Sequence[int]] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.OptionalArgument(
                "for_context",
                parsers.ParserFor.make(SessionRestrictionContext),
                doc="If set and not none this is the course for which the token is valid.",
            ),
            rqa.OptionalArgument(
                "removed_permissions",
                parsers.ParserFor.make(RemovedPermissions),
                doc="The removed permissions for a session.",
            ),
            rqa.OptionalArgument(
                "verified_assignment_ids",
                rqa.List(rqa.SimpleValue.int),
                doc="Assignments with password access restriction.",
            ),
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.for_context = maybe_from_nullable(self.for_context)
        self.removed_permissions = maybe_from_nullable(
            self.removed_permissions
        )
        self.verified_assignment_ids = maybe_from_nullable(
            self.verified_assignment_ids
        )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {}
        if self.for_context.is_just:
            res["for_context"] = to_dict(self.for_context.value)
        if self.removed_permissions.is_just:
            res["removed_permissions"] = to_dict(
                self.removed_permissions.value
            )
        if self.verified_assignment_ids.is_just:
            res["verified_assignment_ids"] = to_dict(
                self.verified_assignment_ids.value
            )
        return res

    @classmethod
    def from_dict(
        cls: t.Type[SessionRestrictionData], d: t.Dict[str, t.Any]
    ) -> SessionRestrictionData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            for_context=parsed.for_context,
            removed_permissions=parsed.removed_permissions,
            verified_assignment_ids=parsed.verified_assignment_ids,
        )
        res.raw_data = d
        return res
