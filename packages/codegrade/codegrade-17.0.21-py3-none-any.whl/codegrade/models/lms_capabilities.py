"""The module that defines the ``LMSCapabilities`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from ..utils import to_dict
from .base_lms_capabilities import BaseLMSCapabilities


@dataclass
class LMSCapabilities(BaseLMSCapabilities):
    """The extra no longer used fields for LMS capabilities."""

    #: Deprecated, should no longer be used.
    test_student_name: Maybe[t.Optional[str]] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseLMSCapabilities.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.OptionalArgument(
                    "test_student_name",
                    rqa.Nullable(rqa.SimpleValue.str),
                    doc="Deprecated, should no longer be used.",
                ),
            )
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.test_student_name = maybe_from_nullable(self.test_student_name)

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "lms": to_dict(self.lms),
            "set_deadline": to_dict(self.set_deadline),
            "set_lock_date": to_dict(self.set_lock_date),
            "set_state": to_dict(self.set_state),
            "set_available_at": to_dict(self.set_available_at),
            "set_name": to_dict(self.set_name),
            "set_max_attempts": to_dict(self.set_max_attempts),
            "cookie_post_message": to_dict(self.cookie_post_message),
            "supported_custom_replacement_groups": to_dict(
                self.supported_custom_replacement_groups
            ),
            "use_id_in_urls": to_dict(self.use_id_in_urls),
            "actual_deep_linking_required": to_dict(
                self.actual_deep_linking_required
            ),
            "auth_audience_required": to_dict(self.auth_audience_required),
        }
        if self.test_student_name.is_just:
            res["test_student_name"] = to_dict(self.test_student_name.value)
        return res

    @classmethod
    def from_dict(
        cls: t.Type[LMSCapabilities], d: t.Dict[str, t.Any]
    ) -> LMSCapabilities:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            lms=parsed.lms,
            set_deadline=parsed.set_deadline,
            set_lock_date=parsed.set_lock_date,
            set_state=parsed.set_state,
            set_available_at=parsed.set_available_at,
            set_name=parsed.set_name,
            set_max_attempts=parsed.set_max_attempts,
            cookie_post_message=parsed.cookie_post_message,
            supported_custom_replacement_groups=parsed.supported_custom_replacement_groups,
            use_id_in_urls=parsed.use_id_in_urls,
            actual_deep_linking_required=parsed.actual_deep_linking_required,
            auth_audience_required=parsed.auth_audience_required,
            test_student_name=parsed.test_student_name,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    pass
