"""The module that defines the ``LTIDeepLinkResponse`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class LTIDeepLinkResponse:
    """The data for deep linking an LTI assignment."""

    #: The url you should use to post the given `jwt` to.
    url: str
    #: The JWT that should be posted to the outputted `url`.
    jwt: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "url",
                rqa.SimpleValue.str,
                doc="The url you should use to post the given `jwt` to.",
            ),
            rqa.RequiredArgument(
                "jwt",
                rqa.SimpleValue.str,
                doc="The JWT that should be posted to the outputted `url`.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "url": to_dict(self.url),
            "jwt": to_dict(self.jwt),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[LTIDeepLinkResponse], d: t.Dict[str, t.Any]
    ) -> LTIDeepLinkResponse:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            url=parsed.url,
            jwt=parsed.jwt,
        )
        res.raw_data = d
        return res
