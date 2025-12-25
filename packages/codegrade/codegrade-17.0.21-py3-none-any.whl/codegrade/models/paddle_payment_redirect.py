"""The module that defines the ``PaddlePaymentRedirect`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class PaddlePaymentRedirect:
    """URL to redirect to after a Paddle payment."""

    #: The URL to redirect to.
    url: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "url",
                rqa.SimpleValue.str,
                doc="The URL to redirect to.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "url": to_dict(self.url),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PaddlePaymentRedirect], d: t.Dict[str, t.Any]
    ) -> PaddlePaymentRedirect:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            url=parsed.url,
        )
        res.raw_data = d
        return res
