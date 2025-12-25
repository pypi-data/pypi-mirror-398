"""The module that defines the ``RateLimitExceededException`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from httpx import Response

from ..utils import to_dict
from .base_error import BaseError


@dataclass
class RateLimitExceededException(BaseError):
    """JSON representation of the exception, extending base APIException.

    We use retry_after, defined with server time so that waiting for that
    period of time will guarantee that you are able to try again.
    """

    #: Relative delay in seconds when you can to try again
    retry_after: datetime.timedelta

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseError.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "retry_after",
                    rqa.RichValue.TimeDelta,
                    doc="Relative delay in seconds when you can to try again",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "retry_after": to_dict(self.retry_after),
            "message": to_dict(self.message),
            "description": to_dict(self.description),
            "code": to_dict(self.code),
            "request_id": to_dict(self.request_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[RateLimitExceededException],
        d: t.Dict[str, t.Any],
        response: t.Optional[Response] = None,
    ) -> RateLimitExceededException:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            retry_after=parsed.retry_after,
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
