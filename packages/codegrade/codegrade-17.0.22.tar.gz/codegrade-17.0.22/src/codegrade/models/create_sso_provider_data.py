"""The module that defines the ``CreateSSOProviderData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class CreateSSOProviderData:
    """Input data required for the `SSO Provider::Create` operation."""

    #: The url where to find the metadata
    metadata_url: str
    #: The fallback description to show if not found in the metadata
    description: str
    #: The tenant that will use this provider
    tenant_id: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "metadata_url",
                rqa.SimpleValue.str,
                doc="The url where to find the metadata",
            ),
            rqa.RequiredArgument(
                "description",
                rqa.SimpleValue.str,
                doc="The fallback description to show if not found in the metadata",
            ),
            rqa.RequiredArgument(
                "tenant_id",
                rqa.SimpleValue.str,
                doc="The tenant that will use this provider",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "metadata_url": to_dict(self.metadata_url),
            "description": to_dict(self.description),
            "tenant_id": to_dict(self.tenant_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CreateSSOProviderData], d: t.Dict[str, t.Any]
    ) -> CreateSSOProviderData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            metadata_url=parsed.metadata_url,
            description=parsed.description,
            tenant_id=parsed.tenant_id,
        )
        res.raw_data = d
        return res
