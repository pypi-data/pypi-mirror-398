"""The module that defines the ``Fraction`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import fractions as f
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..utils import to_dict


@dataclass
class Fraction(f.Fraction):
    """The JSON representation of a fraction"""

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "n",
                rqa.QueryParam.int,
                doc="The numerator of the rational.",
            ),
            rqa.RequiredArgument(
                "d",
                rqa.QueryParam.int,
                doc="The denominator of the rational.",
            ),
        ).use_readable_describe(True)
    )

    def __new__(
        cls, n: int, d: int, raw_data: t.Dict[str, t.Any]
    ) -> "Fraction":
        self = super(Fraction, cls).__new__(cls, numerator=n, denominator=d)
        self.raw_data = raw_data
        return self

    def to_dict(self) -> t.Dict[str, t.Any]:
        return to_dict(self)

    @classmethod
    def from_dict(cls: t.Type[Fraction], d: t.Dict[str, t.Any]) -> "Fraction":
        parsed = cls.data_parser.try_parse(d)
        res = cls.__new__(cls, parsed.n, parsed.d, d)
        return res
