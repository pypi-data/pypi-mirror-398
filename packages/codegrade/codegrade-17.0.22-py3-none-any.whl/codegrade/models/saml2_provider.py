"""The module that defines the ``Saml2Provider`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .saml_ui_info import SamlUiInfo


@dataclass
class Saml2Provider:
    """The serialization of a `Saml2Provider`."""

    #: The `id` of the provider.
    id: str
    #: The url of the metadata of the IdP connected to this provider.
    metadata_url: str
    #: Information about the IdP and how to display it to the user.
    ui_info: SamlUiInfo

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "id",
                rqa.SimpleValue.str,
                doc="The `id` of the provider.",
            ),
            rqa.RequiredArgument(
                "metadata_url",
                rqa.SimpleValue.str,
                doc="The url of the metadata of the IdP connected to this provider.",
            ),
            rqa.RequiredArgument(
                "ui_info",
                parsers.ParserFor.make(SamlUiInfo),
                doc="Information about the IdP and how to display it to the user.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "metadata_url": to_dict(self.metadata_url),
            "ui_info": to_dict(self.ui_info),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[Saml2Provider], d: t.Dict[str, t.Any]
    ) -> Saml2Provider:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            metadata_url=parsed.metadata_url,
            ui_info=parsed.ui_info,
        )
        res.raw_data = d
        return res
