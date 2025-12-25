"""The module that defines the ``RepositoryConnectionLimitReachedException`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from httpx import Response

from ..utils import to_dict
from .base_error import BaseError


@dataclass
class RepositoryConnectionLimitReachedException(BaseError):
    """The exception used trying to connect a repository to an assignment that
    already has one.
    """

    #: Id of the webhook that causes the error.
    webhook_id: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseError.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "webhook_id",
                    rqa.SimpleValue.str,
                    doc="Id of the webhook that causes the error.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "webhook_id": to_dict(self.webhook_id),
            "message": to_dict(self.message),
            "description": to_dict(self.description),
            "code": to_dict(self.code),
            "request_id": to_dict(self.request_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[RepositoryConnectionLimitReachedException],
        d: t.Dict[str, t.Any],
        response: t.Optional[Response] = None,
    ) -> RepositoryConnectionLimitReachedException:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            webhook_id=parsed.webhook_id,
            message=parsed.message,
            description=parsed.description,
            code=parsed.code,
            request_id=parsed.request_id,
            response=response,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    from .api_codes import APICodes
