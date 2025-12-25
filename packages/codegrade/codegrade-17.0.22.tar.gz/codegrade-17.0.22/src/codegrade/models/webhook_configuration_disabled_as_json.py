"""The module that defines the ``WebhookConfigurationDisabledAsJSON`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class WebhookConfigurationDisabledAsJSON:
    """Webhook upload type is disabled."""

    #: The tag for this data.
    tag: t.Literal["disabled"]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "tag",
                rqa.StringEnum("disabled"),
                doc="The tag for this data.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tag": to_dict(self.tag),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[WebhookConfigurationDisabledAsJSON], d: t.Dict[str, t.Any]
    ) -> WebhookConfigurationDisabledAsJSON:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tag=parsed.tag,
        )
        res.raw_data = d
        return res
