"""The module that defines the ``PlagiarismMatch`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .base_directory import BaseDirectory
from .base_file import BaseFile


@dataclass
class PlagiarismMatch:
    """A single plagiarism match, this is a hunk of code that look similar."""

    #: The id of this match.
    id: int
    #: The two files that construct this match. This list always has a length
    #: of 2.
    files: t.Sequence[t.Union[BaseFile, BaseDirectory]]
    #: The lines that match in each file, item in this list (which always has a
    #: length of 2) is the start,end tuple.
    lines: t.Sequence[t.Sequence[t.Union[int]]]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "id",
                rqa.SimpleValue.int,
                doc="The id of this match.",
            ),
            rqa.RequiredArgument(
                "files",
                rqa.List(
                    parsers.make_union(
                        parsers.ParserFor.make(BaseFile),
                        parsers.ParserFor.make(BaseDirectory),
                    )
                ),
                doc="The two files that construct this match. This list always has a length of 2.",
            ),
            rqa.RequiredArgument(
                "lines",
                rqa.List(rqa.List(parsers.make_union(rqa.SimpleValue.int))),
                doc="The lines that match in each file, item in this list (which always has a length of 2) is the start,end tuple.",
            ),
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "id": to_dict(self.id),
            "files": to_dict(self.files),
            "lines": to_dict(self.lines),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PlagiarismMatch], d: t.Dict[str, t.Any]
    ) -> PlagiarismMatch:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            id=parsed.id,
            files=parsed.files,
            lines=parsed.lines,
        )
        res.raw_data = d
        return res
