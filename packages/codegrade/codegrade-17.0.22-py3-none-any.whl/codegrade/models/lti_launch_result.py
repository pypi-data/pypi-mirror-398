"""The module that defines the ``LTILaunchResult`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .lti_assignment_launch_data import LTIAssignmentLaunchData
from .lti_deep_link_result import LTIDeepLinkResult
from .lti_template_preview_launch_data import LTITemplatePreviewLaunchData
from .lti_version import LTIVersion


@dataclass
class LTILaunchResult:
    """The result of an LTI launch with the version attached."""

    #: Information about what we have successfully launched.
    data: t.Union[
        LTIAssignmentLaunchData,
        LTITemplatePreviewLaunchData,
        LTIDeepLinkResult,
    ]
    #: The version of LTI we have used for the launch.
    version: LTIVersion

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "data",
                parsers.make_union(
                    parsers.ParserFor.make(LTIAssignmentLaunchData),
                    parsers.ParserFor.make(LTITemplatePreviewLaunchData),
                    parsers.ParserFor.make(LTIDeepLinkResult),
                ),
                doc="Information about what we have successfully launched.",
            ),
            rqa.RequiredArgument(
                "version",
                rqa.EnumValue(LTIVersion),
                doc="The version of LTI we have used for the launch.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "data": to_dict(self.data),
            "version": to_dict(self.version),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[LTILaunchResult], d: t.Dict[str, t.Any]
    ) -> LTILaunchResult:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            data=parsed.data,
            version=parsed.version,
        )
        res.raw_data = d
        return res
