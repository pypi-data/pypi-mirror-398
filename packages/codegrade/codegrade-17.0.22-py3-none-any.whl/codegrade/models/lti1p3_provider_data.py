"""The module that defines the ``LTI1p3ProviderData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from ..utils import to_dict


@dataclass
class LTI1p3ProviderData:
    """ """

    #: The id of the tenant that will use this LMS
    tenant_id: str
    #: The iss of the new provider
    iss: str
    #: The LMS that will be used for this connection
    lms: t.Literal[
        "Canvas",
        "Blackboard",
        "Moodle",
        "Brightspace",
        "Revel",
        "XL",
        "Bronte",
    ]
    #: Use LTI 1.3
    lti_version: t.Literal["lti1.3"]
    #: Label for the LTI provider
    label: Maybe[str] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "tenant_id",
                rqa.SimpleValue.str,
                doc="The id of the tenant that will use this LMS",
            ),
            rqa.RequiredArgument(
                "iss",
                rqa.SimpleValue.str,
                doc="The iss of the new provider",
            ),
            rqa.RequiredArgument(
                "lms",
                rqa.StringEnum(
                    "Canvas",
                    "Blackboard",
                    "Moodle",
                    "Brightspace",
                    "Revel",
                    "XL",
                    "Bronte",
                ),
                doc="The LMS that will be used for this connection",
            ),
            rqa.RequiredArgument(
                "lti_version",
                rqa.StringEnum("lti1.3"),
                doc="Use LTI 1.3",
            ),
            rqa.OptionalArgument(
                "label",
                rqa.SimpleValue.str,
                doc="Label for the LTI provider",
            ),
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.label = maybe_from_nullable(self.label)

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "tenant_id": to_dict(self.tenant_id),
            "iss": to_dict(self.iss),
            "lms": to_dict(self.lms),
            "lti_version": to_dict(self.lti_version),
        }
        if self.label.is_just:
            res["label"] = to_dict(self.label.value)
        return res

    @classmethod
    def from_dict(
        cls: t.Type[LTI1p3ProviderData], d: t.Dict[str, t.Any]
    ) -> LTI1p3ProviderData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            tenant_id=parsed.tenant_id,
            iss=parsed.iss,
            lms=parsed.lms,
            lti_version=parsed.lti_version,
            label=parsed.label,
        )
        res.raw_data = d
        return res
