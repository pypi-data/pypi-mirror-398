"""The module that defines the ``SamlUiInfo`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .saml_ui_logo_info import SamlUiLogoInfo


@dataclass
class SamlUiInfo:
    """A dictionary representing UI info about a Identity Provider (IdP)."""

    #: The name of the SAML IdP
    name: str
    #: The description of the provider.
    description: str
    #: Optionally a logo of the provider.
    logo: t.Optional[SamlUiLogoInfo]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "name",
                rqa.SimpleValue.str,
                doc="The name of the SAML IdP",
            ),
            rqa.RequiredArgument(
                "description",
                rqa.SimpleValue.str,
                doc="The description of the provider.",
            ),
            rqa.RequiredArgument(
                "logo",
                rqa.Nullable(parsers.ParserFor.make(SamlUiLogoInfo)),
                doc="Optionally a logo of the provider.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "name": to_dict(self.name),
            "description": to_dict(self.description),
            "logo": to_dict(self.logo),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[SamlUiInfo], d: t.Dict[str, t.Any]
    ) -> SamlUiInfo:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            name=parsed.name,
            description=parsed.description,
            logo=parsed.logo,
        )
        res.raw_data = d
        return res
