"""The module that defines the ``CreateTenantData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .json_create_tenant import JsonCreateTenant
from .types import File


@dataclass
class CreateTenantData:
    """Input data required for the `Tenant::Create` operation."""

    json: JsonCreateTenant
    logo_default: File
    logo_dark: File

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "json",
                parsers.ParserFor.make(JsonCreateTenant),
                doc="",
            ),
            rqa.RequiredArgument(
                "logo-default",
                rqa.AnyValue,
                doc="",
            ),
            rqa.RequiredArgument(
                "logo-dark",
                rqa.AnyValue,
                doc="",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "json": to_dict(self.json),
            "logo-default": to_dict(self.logo_default),
            "logo-dark": to_dict(self.logo_dark),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CreateTenantData], d: t.Dict[str, t.Any]
    ) -> CreateTenantData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            json=parsed.json,
            logo_default=getattr(parsed, "logo-default"),
            logo_dark=getattr(parsed, "logo-dark"),
        )
        res.raw_data = d
        return res
