"""The module that defines the ``Tenant`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class Tenant:
    """The JSON representation of a tenant."""

    #: The id of the tenant
    id: str
    #: The name of the tenant
    name: str
    #: Maybe the id of the SSO provider connected to this tenant.
    sso_provider_id: t.Optional[str]
    #: The short name (or names) of the tenant. This is used to make searching
    #: for tenants by end users easier.
    abbreviated_name: t.Optional[str]
    #: This value determines how the tenant should be ordered. Tenants should
    #: first be ordered from highest `order_category` to lowest, and then by
    #: name.
    order_category: int
    #: This value states whether the tenant should be hidden from listing if
    #: the user is not allowed to see hidden tenants.
    is_hidden: bool
    #: The netloc this tenant is hosted on.
    netloc: str
    #: A url where you can download the default logo for this tenant. You don't
    #: need to be logged in to use this url.
    logo_default_url: str
    #: A url where you can download the dark logo for this tenant. You don't
    #: need to be logged in to use this url.
    logo_dark_url: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "id",
                rqa.SimpleValue.str,
                doc="The id of the tenant",
            ),
            rqa.RequiredArgument(
                "name",
                rqa.SimpleValue.str,
                doc="The name of the tenant",
            ),
            rqa.RequiredArgument(
                "sso_provider_id",
                rqa.Nullable(rqa.SimpleValue.str),
                doc="Maybe the id of the SSO provider connected to this tenant.",
            ),
            rqa.RequiredArgument(
                "abbreviated_name",
                rqa.Nullable(rqa.SimpleValue.str),
                doc="The short name (or names) of the tenant. This is used to make searching for tenants by end users easier.",
            ),
            rqa.RequiredArgument(
                "order_category",
                rqa.SimpleValue.int,
                doc="This value determines how the tenant should be ordered. Tenants should first be ordered from highest `order_category` to lowest, and then by name.",
            ),
            rqa.RequiredArgument(
                "is_hidden",
                rqa.SimpleValue.bool,
                doc="This value states whether the tenant should be hidden from listing if the user is not allowed to see hidden tenants.",
            ),
            rqa.RequiredArgument(
                "netloc",
                rqa.SimpleValue.str,
                doc="The netloc this tenant is hosted on.",
            ),
            rqa.RequiredArgument(
                "logo_default_url",
                rqa.SimpleValue.str,
                doc="A url where you can download the default logo for this tenant. You don't need to be logged in to use this url.",
            ),
            rqa.RequiredArgument(
                "logo_dark_url",
                rqa.SimpleValue.str,
                doc="A url where you can download the dark logo for this tenant. You don't need to be logged in to use this url.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "name": to_dict(self.name),
            "sso_provider_id": to_dict(self.sso_provider_id),
            "abbreviated_name": to_dict(self.abbreviated_name),
            "order_category": to_dict(self.order_category),
            "is_hidden": to_dict(self.is_hidden),
            "netloc": to_dict(self.netloc),
            "logo_default_url": to_dict(self.logo_default_url),
            "logo_dark_url": to_dict(self.logo_dark_url),
        }
        return res

    @classmethod
    def from_dict(cls: t.Type[Tenant], d: t.Dict[str, t.Any]) -> Tenant:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            name=parsed.name,
            sso_provider_id=parsed.sso_provider_id,
            abbreviated_name=parsed.abbreviated_name,
            order_category=parsed.order_category,
            is_hidden=parsed.is_hidden,
            netloc=parsed.netloc,
            logo_default_url=parsed.logo_default_url,
            logo_dark_url=parsed.logo_dark_url,
        )
        res.raw_data = d
        return res
