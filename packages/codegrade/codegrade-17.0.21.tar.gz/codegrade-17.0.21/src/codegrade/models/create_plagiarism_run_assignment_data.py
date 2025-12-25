"""The module that defines the ``CreatePlagiarismRunAssignmentData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from .. import parsers
from ..utils import to_dict
from .create_plagiarism_run_data import CreatePlagiarismRunData
from .types import File


@dataclass
class CreatePlagiarismRunAssignmentData:
    """Input data required for the `Assignment::CreatePlagiarismRun` operation."""

    json: CreatePlagiarismRunData
    base_code: Maybe[File] = Nothing
    old_submissions: Maybe[File] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.RequiredArgument(
                "json",
                parsers.ParserFor.make(CreatePlagiarismRunData),
                doc="",
            ),
            rqa.OptionalArgument(
                "base_code",
                rqa.AnyValue,
                doc="",
            ),
            rqa.OptionalArgument(
                "old_submissions",
                rqa.AnyValue,
                doc="",
            ),
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.base_code = maybe_from_nullable(self.base_code)
        self.old_submissions = maybe_from_nullable(self.old_submissions)

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "json": to_dict(self.json),
        }
        if self.base_code.is_just:
            res["base_code"] = to_dict(self.base_code.value)
        if self.old_submissions.is_just:
            res["old_submissions"] = to_dict(self.old_submissions.value)
        return res

    @classmethod
    def from_dict(
        cls: t.Type[CreatePlagiarismRunAssignmentData], d: t.Dict[str, t.Any]
    ) -> CreatePlagiarismRunAssignmentData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            json=parsed.json,
            base_code=parsed.base_code,
            old_submissions=parsed.old_submissions,
        )
        res.raw_data = d
        return res
