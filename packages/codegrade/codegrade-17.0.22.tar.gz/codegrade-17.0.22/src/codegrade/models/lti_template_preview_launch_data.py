"""The module that defines the ``LTITemplatePreviewLaunchData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .base_launch_data import BaseLaunchData
from .pearson_template import PearsonTemplate


@dataclass
class LTITemplatePreviewLaunchData(BaseLaunchData):
    """This is the data returned to the client after a successful LTI launch."""

    #: Always `template_result`.
    type: t.Literal["template_preview_result"]
    #: The template launched in preview mode.
    template: PearsonTemplate

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseLaunchData.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "type",
                    rqa.StringEnum("template_preview_result"),
                    doc="Always `template_result`.",
                ),
                rqa.RequiredArgument(
                    "template",
                    parsers.ParserFor.make(PearsonTemplate),
                    doc="The template launched in preview mode.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "type": to_dict(self.type),
            "template": to_dict(self.template),
            "course": to_dict(self.course),
            "new_role_created": to_dict(self.new_role_created),
            "new_session": to_dict(self.new_session),
            "updated_email": to_dict(self.updated_email),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[LTITemplatePreviewLaunchData], d: t.Dict[str, t.Any]
    ) -> LTITemplatePreviewLaunchData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            type=parsed.type,
            template=parsed.template,
            course=parsed.course,
            new_role_created=parsed.new_role_created,
            new_session=parsed.new_session,
            updated_email=parsed.updated_email,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    from .extended_course import ExtendedCourse
    from .user_login_response import UserLoginResponse
