"""The module that defines the ``WebhookConfigurationEnabledAsJSON`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class WebhookConfigurationEnabledAsJSON:
    """Webhook upload type is enabled."""

    #: The tag for this data.
    tag: t.Literal["enabled"]
    #: A url for a repository that determine the template for student
    #: submissions.
    template_url: t.Optional[str]
    #: The token to use for the template connection. It is present only for
    #: private template repository.
    template_token_id: t.Optional[str]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "tag",
                rqa.StringEnum("enabled"),
                doc="The tag for this data.",
            ),
            rqa.RequiredArgument(
                "template_url",
                rqa.Nullable(rqa.SimpleValue.str),
                doc="A url for a repository that determine the template for student submissions.",
            ),
            rqa.RequiredArgument(
                "template_token_id",
                rqa.Nullable(rqa.SimpleValue.str),
                doc="The token to use for the template connection. It is present only for private template repository.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tag": to_dict(self.tag),
            "template_url": to_dict(self.template_url),
            "template_token_id": to_dict(self.template_token_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[WebhookConfigurationEnabledAsJSON], d: t.Dict[str, t.Any]
    ) -> WebhookConfigurationEnabledAsJSON:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tag=parsed.tag,
            template_url=parsed.template_url,
            template_token_id=parsed.template_token_id,
        )
        res.raw_data = d
        return res
