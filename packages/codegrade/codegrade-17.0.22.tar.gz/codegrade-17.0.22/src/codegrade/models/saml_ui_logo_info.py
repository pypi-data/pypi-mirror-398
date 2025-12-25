"""The module that defines the ``SamlUiLogoInfo`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class SamlUiLogoInfo:
    """The data that describes the logo for a SAML provider."""

    #: The URL where you can download the logo.
    url: str
    #: The width of the logo.
    width: int
    #: The height of the logo.
    height: int

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "url",
                rqa.SimpleValue.str,
                doc="The URL where you can download the logo.",
            ),
            rqa.RequiredArgument(
                "width",
                rqa.SimpleValue.int,
                doc="The width of the logo.",
            ),
            rqa.RequiredArgument(
                "height",
                rqa.SimpleValue.int,
                doc="The height of the logo.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "url": to_dict(self.url),
            "width": to_dict(self.width),
            "height": to_dict(self.height),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[SamlUiLogoInfo], d: t.Dict[str, t.Any]
    ) -> SamlUiLogoInfo:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            url=parsed.url,
            width=parsed.width,
            height=parsed.height,
        )
        res.raw_data = d
        return res
