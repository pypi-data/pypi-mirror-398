"""The module that defines the ``BaseAbout`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .frontend_site_settings import FrontendSiteSettings
from .release_info import ReleaseInfo


@dataclass
class BaseAbout:
    """The base information about this instance."""

    #: The commit this server is running. Deprecated, please use
    #: `release.commit` instead.
    commit: str
    #: The frontend settings and their values for this instance.
    settings: FrontendSiteSettings
    #: Information about the release running on this server.
    release: ReleaseInfo
    #: The current time on the server
    current_time: datetime.datetime

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "commit",
                rqa.SimpleValue.str,
                doc="The commit this server is running. Deprecated, please use `release.commit` instead.",
            ),
            rqa.RequiredArgument(
                "settings",
                parsers.ParserFor.make(FrontendSiteSettings),
                doc="The frontend settings and their values for this instance.",
            ),
            rqa.RequiredArgument(
                "release",
                parsers.ParserFor.make(ReleaseInfo),
                doc="Information about the release running on this server.",
            ),
            rqa.RequiredArgument(
                "current_time",
                rqa.RichValue.DateTime,
                doc="The current time on the server",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "commit": to_dict(self.commit),
            "settings": to_dict(self.settings),
            "release": to_dict(self.release),
            "current_time": to_dict(self.current_time),
        }
        return res

    @classmethod
    def from_dict(cls: t.Type[BaseAbout], d: t.Dict[str, t.Any]) -> BaseAbout:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            commit=parsed.commit,
            settings=parsed.settings,
            release=parsed.release,
            current_time=parsed.current_time,
        )
        res.raw_data = d
        return res
