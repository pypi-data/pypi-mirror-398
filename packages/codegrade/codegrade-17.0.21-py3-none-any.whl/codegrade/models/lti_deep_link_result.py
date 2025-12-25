"""The module that defines the ``LTIDeepLinkResult`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class LTIDeepLinkResult:
    """The result of a LTI launch when an actual deep link is required."""

    #: Always `"deep_link"`.
    type: t.Literal["deep_link"]
    #: The id of the blob that stores the deep link information.
    deep_link_blob_id: str
    #: The authentication token you can use to finish the LTI deep link later.
    auth_token: str

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "type",
                rqa.StringEnum("deep_link"),
                doc='Always `"deep_link"`.',
            ),
            rqa.RequiredArgument(
                "deep_link_blob_id",
                rqa.SimpleValue.str,
                doc="The id of the blob that stores the deep link information.",
            ),
            rqa.RequiredArgument(
                "auth_token",
                rqa.SimpleValue.str,
                doc="The authentication token you can use to finish the LTI deep link later.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "type": to_dict(self.type),
            "deep_link_blob_id": to_dict(self.deep_link_blob_id),
            "auth_token": to_dict(self.auth_token),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[LTIDeepLinkResult], d: t.Dict[str, t.Any]
    ) -> LTIDeepLinkResult:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            type=parsed.type,
            deep_link_blob_id=parsed.deep_link_blob_id,
            auth_token=parsed.auth_token,
        )
        res.raw_data = d
        return res
