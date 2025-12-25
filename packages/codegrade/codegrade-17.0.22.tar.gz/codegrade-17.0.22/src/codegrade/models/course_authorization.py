"""The module that defines the ``CourseAuthorization`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .access_expired import AccessExpired
from .access_granted import AccessGranted
from .access_revoked import AccessRevoked
from .course_perm_map import CoursePermMap
from .no_payment_required import NoPaymentRequired
from .payment_required import PaymentRequired
from .transaction_pending import TransactionPending


@dataclass
class CourseAuthorization:
    """The authorization a user has in a course"""

    #: Does this user still need to pay for the course.
    payment_status: t.Union[
        AccessExpired,
        PaymentRequired,
        TransactionPending,
        AccessGranted,
        AccessRevoked,
        NoPaymentRequired,
    ]
    #: The permissions the user has in the course.
    permissions: CoursePermMap

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "payment_status",
                parsers.make_union(
                    parsers.ParserFor.make(AccessExpired),
                    parsers.ParserFor.make(PaymentRequired),
                    parsers.ParserFor.make(TransactionPending),
                    parsers.ParserFor.make(AccessGranted),
                    parsers.ParserFor.make(AccessRevoked),
                    parsers.ParserFor.make(NoPaymentRequired),
                ),
                doc="Does this user still need to pay for the course.",
            ),
            rqa.RequiredArgument(
                "permissions",
                parsers.ParserFor.make(CoursePermMap),
                doc="The permissions the user has in the course.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "payment_status": to_dict(self.payment_status),
            "permissions": to_dict(self.permissions),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CourseAuthorization], d: t.Dict[str, t.Any]
    ) -> CourseAuthorization:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            payment_status=parsed.payment_status,
            permissions=parsed.permissions,
        )
        res.raw_data = d
        return res
