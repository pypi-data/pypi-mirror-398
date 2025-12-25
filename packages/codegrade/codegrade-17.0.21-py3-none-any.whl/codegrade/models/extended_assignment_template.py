"""The module that defines the ``ExtendedAssignmentTemplate`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .assignment_template import AssignmentTemplate
from .file_tree import FileTree, FileTreeParser


@dataclass
class ExtendedAssignmentTemplate(AssignmentTemplate):
    """The extended version of an assignment template."""

    #: The files of this template.
    files: t.Optional[FileTree]

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: AssignmentTemplate.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "files",
                    rqa.Nullable(FileTreeParser),
                    doc="The files of this template.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "files": to_dict(self.files),
            "assignment_id": to_dict(self.assignment_id),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type[ExtendedAssignmentTemplate], d: t.Dict[str, t.Any]
    ) -> ExtendedAssignmentTemplate:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            files=parsed.files,
            assignment_id=parsed.assignment_id,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    pass
