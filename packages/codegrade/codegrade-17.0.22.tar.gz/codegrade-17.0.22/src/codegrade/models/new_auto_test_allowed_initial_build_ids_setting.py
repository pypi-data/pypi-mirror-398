"""The module that defines the ``NewAutoTestAllowedInitialBuildIdsSetting`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class NewAutoTestAllowedInitialBuildIdsSetting:
    """ """

    name: t.Literal["NEW_AUTO_TEST_ALLOWED_INITIAL_BUILD_IDS"]
    value: t.Optional[t.Sequence[str]]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "name",
                rqa.StringEnum("NEW_AUTO_TEST_ALLOWED_INITIAL_BUILD_IDS"),
                doc="",
            ),
            rqa.RequiredArgument(
                "value",
                rqa.Nullable(rqa.List(rqa.SimpleValue.str)),
                doc="",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "name": to_dict(self.name),
            "value": to_dict(self.value),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[NewAutoTestAllowedInitialBuildIdsSetting],
        d: t.Dict[str, t.Any],
    ) -> NewAutoTestAllowedInitialBuildIdsSetting:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            name=parsed.name,
            value=parsed.value,
        )
        res.raw_data = d
        return res
