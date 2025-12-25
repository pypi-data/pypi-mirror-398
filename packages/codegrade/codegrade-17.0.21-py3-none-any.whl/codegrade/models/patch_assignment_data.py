"""The module that defines the ``PatchAssignmentData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from .. import parsers
from ..utils import to_dict
from .assignment_anonymization_algo import AssignmentAnonymizationAlgo
from .assignment_done_type import AssignmentDoneType
from .assignment_kind import AssignmentKind
from .assignment_percentage_grading_settings import (
    AssignmentPercentageGradingSettings,
)
from .assignment_points_grading_settings import AssignmentPointsGradingSettings
from .assignment_submission_mode import AssignmentSubmissionMode
from .fixed_grade_availability import FixedGradeAvailability
from .submission_validator_input_data import SubmissionValidatorInputData


@dataclass
class PatchAssignmentData:
    """Input data required for the `Assignment::Patch` operation."""

    #: The new name of the assignment
    name: Maybe[str] = Nothing
    #: The maximum possible grade for this assignment. You can reset this by
    #: passing `null` as value
    max_grade: Maybe[t.Optional[float]] = Nothing
    #: The group set id for this assignment. Set to `null` to make this
    #: assignment not a group assignment
    group_set_id: Maybe[t.Optional[int]] = Nothing
    #: Should we send login links to students before the assignment opens. This
    #: is only available for assignments with 'kind' equal to 'exam'.
    send_login_links: Maybe[bool] = Nothing
    #: The new kind of assignment
    kind: Maybe[AssignmentKind] = Nothing
    #: Should students be allowed to make submissions by uploading files
    files_upload_enabled: Maybe[bool] = Nothing
    #: Should students be allowed to make submissions using git webhooks
    webhook_upload_enabled: Maybe[bool] = Nothing
    #: The maximum amount of submissions a user may create.
    max_submissions: Maybe[t.Optional[int]] = Nothing
    #: The amount of time in seconds there should be between
    #: `amount_in_cool_off_period + 1` submissions.
    cool_off_period: Maybe[float] = Nothing
    #: The maximum amount of submissions that can be made within
    #: `cool_off_period` seconds. This should be higher than or equal to 1.
    amount_in_cool_off_period: Maybe[int] = Nothing
    #: The ignore file to use
    ignore: Maybe[t.Union[SubmissionValidatorInputData, str]] = Nothing
    #: The ignore version to use, defaults to "IgnoreFilterManager".
    ignore_version: Maybe[
        t.Literal[
            "EmptySubmissionFilter",
            "IgnoreFilterManager",
            "SubmissionValidator",
        ]
    ] = Nothing
    #: How to determine grading is done for this assignment, this value is not
    #: used when `reminder_time` is `null`.
    done_type: Maybe[t.Optional[AssignmentDoneType]] = Nothing
    #: At what time should we send the reminder emails to the graders. This
    #: value is not used when `done_type` is `null`.
    reminder_time: Maybe[t.Optional[datetime.datetime]] = Nothing
    #: A list of emails that should receive an email when grading is done. This
    #: value has no effect when `done_type` is set to `null`.
    done_email: Maybe[t.Optional[str]] = Nothing
    #: Should anonymized grading be enabled for this assignment.
    anonymized_grading: Maybe[t.Optional[AssignmentAnonymizationAlgo]] = (
        Nothing
    )
    #: The file we should load first in an assignment
    file_to_load_first: Maybe[t.Optional[str]] = Nothing
    #: Grading settings of this assignment.
    grading: Maybe[
        t.Union[
            AssignmentPointsGradingSettings,
            AssignmentPercentageGradingSettings,
        ]
    ] = Nothing
    #: The grade availability of this assignment.
    grade_availability: Maybe[FixedGradeAvailability] = Nothing
    #: The submission mode of this assignment
    submission_mode: Maybe[AssignmentSubmissionMode] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.OptionalArgument(
                "name",
                rqa.SimpleValue.str,
                doc="The new name of the assignment",
            ),
            rqa.OptionalArgument(
                "max_grade",
                rqa.Nullable(rqa.SimpleValue.float),
                doc="The maximum possible grade for this assignment. You can reset this by passing `null` as value",
            ),
            rqa.OptionalArgument(
                "group_set_id",
                rqa.Nullable(rqa.SimpleValue.int),
                doc="The group set id for this assignment. Set to `null` to make this assignment not a group assignment",
            ),
            rqa.OptionalArgument(
                "send_login_links",
                rqa.SimpleValue.bool,
                doc="Should we send login links to students before the assignment opens. This is only available for assignments with 'kind' equal to 'exam'.",
            ),
            rqa.OptionalArgument(
                "kind",
                rqa.EnumValue(AssignmentKind),
                doc="The new kind of assignment",
            ),
            rqa.OptionalArgument(
                "files_upload_enabled",
                rqa.SimpleValue.bool,
                doc="Should students be allowed to make submissions by uploading files",
            ),
            rqa.OptionalArgument(
                "webhook_upload_enabled",
                rqa.SimpleValue.bool,
                doc="Should students be allowed to make submissions using git webhooks",
            ),
            rqa.OptionalArgument(
                "max_submissions",
                rqa.Nullable(rqa.SimpleValue.int),
                doc="The maximum amount of submissions a user may create.",
            ),
            rqa.OptionalArgument(
                "cool_off_period",
                rqa.SimpleValue.float,
                doc="The amount of time in seconds there should be between `amount_in_cool_off_period + 1` submissions.",
            ),
            rqa.OptionalArgument(
                "amount_in_cool_off_period",
                rqa.SimpleValue.int,
                doc="The maximum amount of submissions that can be made within `cool_off_period` seconds. This should be higher than or equal to 1.",
            ),
            rqa.OptionalArgument(
                "ignore",
                parsers.make_union(
                    parsers.ParserFor.make(SubmissionValidatorInputData),
                    rqa.SimpleValue.str,
                ),
                doc="The ignore file to use",
            ),
            rqa.OptionalArgument(
                "ignore_version",
                rqa.StringEnum(
                    "EmptySubmissionFilter",
                    "IgnoreFilterManager",
                    "SubmissionValidator",
                ),
                doc='The ignore version to use, defaults to "IgnoreFilterManager".',
            ),
            rqa.OptionalArgument(
                "done_type",
                rqa.Nullable(rqa.EnumValue(AssignmentDoneType)),
                doc="How to determine grading is done for this assignment, this value is not used when `reminder_time` is `null`.",
            ),
            rqa.OptionalArgument(
                "reminder_time",
                rqa.Nullable(rqa.RichValue.DateTime),
                doc="At what time should we send the reminder emails to the graders. This value is not used when `done_type` is `null`.",
            ),
            rqa.OptionalArgument(
                "done_email",
                rqa.Nullable(rqa.SimpleValue.str),
                doc="A list of emails that should receive an email when grading is done. This value has no effect when `done_type` is set to `null`.",
            ),
            rqa.OptionalArgument(
                "anonymized_grading",
                rqa.Nullable(rqa.EnumValue(AssignmentAnonymizationAlgo)),
                doc="Should anonymized grading be enabled for this assignment.",
            ),
            rqa.OptionalArgument(
                "file_to_load_first",
                rqa.Nullable(rqa.SimpleValue.str),
                doc="The file we should load first in an assignment",
            ),
            rqa.OptionalArgument(
                "grading",
                parsers.make_union(
                    parsers.ParserFor.make(AssignmentPointsGradingSettings),
                    parsers.ParserFor.make(
                        AssignmentPercentageGradingSettings
                    ),
                ),
                doc="Grading settings of this assignment.",
            ),
            rqa.OptionalArgument(
                "grade_availability",
                parsers.ParserFor.make(FixedGradeAvailability),
                doc="The grade availability of this assignment.",
            ),
            rqa.OptionalArgument(
                "submission_mode",
                rqa.EnumValue(AssignmentSubmissionMode),
                doc="The submission mode of this assignment",
            ),
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.name = maybe_from_nullable(self.name)
        self.max_grade = maybe_from_nullable(self.max_grade)
        self.group_set_id = maybe_from_nullable(self.group_set_id)
        self.send_login_links = maybe_from_nullable(self.send_login_links)
        self.kind = maybe_from_nullable(self.kind)
        self.files_upload_enabled = maybe_from_nullable(
            self.files_upload_enabled
        )
        self.webhook_upload_enabled = maybe_from_nullable(
            self.webhook_upload_enabled
        )
        self.max_submissions = maybe_from_nullable(self.max_submissions)
        self.cool_off_period = maybe_from_nullable(self.cool_off_period)
        self.amount_in_cool_off_period = maybe_from_nullable(
            self.amount_in_cool_off_period
        )
        self.ignore = maybe_from_nullable(self.ignore)
        self.ignore_version = maybe_from_nullable(self.ignore_version)
        self.done_type = maybe_from_nullable(self.done_type)
        self.reminder_time = maybe_from_nullable(self.reminder_time)
        self.done_email = maybe_from_nullable(self.done_email)
        self.anonymized_grading = maybe_from_nullable(self.anonymized_grading)
        self.file_to_load_first = maybe_from_nullable(self.file_to_load_first)
        self.grading = maybe_from_nullable(self.grading)
        self.grade_availability = maybe_from_nullable(self.grade_availability)
        self.submission_mode = maybe_from_nullable(self.submission_mode)

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {}
        if self.name.is_just:
            res["name"] = to_dict(self.name.value)
        if self.max_grade.is_just:
            res["max_grade"] = to_dict(self.max_grade.value)
        if self.group_set_id.is_just:
            res["group_set_id"] = to_dict(self.group_set_id.value)
        if self.send_login_links.is_just:
            res["send_login_links"] = to_dict(self.send_login_links.value)
        if self.kind.is_just:
            res["kind"] = to_dict(self.kind.value)
        if self.files_upload_enabled.is_just:
            res["files_upload_enabled"] = to_dict(
                self.files_upload_enabled.value
            )
        if self.webhook_upload_enabled.is_just:
            res["webhook_upload_enabled"] = to_dict(
                self.webhook_upload_enabled.value
            )
        if self.max_submissions.is_just:
            res["max_submissions"] = to_dict(self.max_submissions.value)
        if self.cool_off_period.is_just:
            res["cool_off_period"] = to_dict(self.cool_off_period.value)
        if self.amount_in_cool_off_period.is_just:
            res["amount_in_cool_off_period"] = to_dict(
                self.amount_in_cool_off_period.value
            )
        if self.ignore.is_just:
            res["ignore"] = to_dict(self.ignore.value)
        if self.ignore_version.is_just:
            res["ignore_version"] = to_dict(self.ignore_version.value)
        if self.done_type.is_just:
            res["done_type"] = to_dict(self.done_type.value)
        if self.reminder_time.is_just:
            res["reminder_time"] = to_dict(self.reminder_time.value)
        if self.done_email.is_just:
            res["done_email"] = to_dict(self.done_email.value)
        if self.anonymized_grading.is_just:
            res["anonymized_grading"] = to_dict(self.anonymized_grading.value)
        if self.file_to_load_first.is_just:
            res["file_to_load_first"] = to_dict(self.file_to_load_first.value)
        if self.grading.is_just:
            res["grading"] = to_dict(self.grading.value)
        if self.grade_availability.is_just:
            res["grade_availability"] = to_dict(self.grade_availability.value)
        if self.submission_mode.is_just:
            res["submission_mode"] = to_dict(self.submission_mode.value)
        return res

    @classmethod
    def from_dict(
        cls: t.Type[PatchAssignmentData], d: t.Dict[str, t.Any]
    ) -> PatchAssignmentData:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            name=parsed.name,
            max_grade=parsed.max_grade,
            group_set_id=parsed.group_set_id,
            send_login_links=parsed.send_login_links,
            kind=parsed.kind,
            files_upload_enabled=parsed.files_upload_enabled,
            webhook_upload_enabled=parsed.webhook_upload_enabled,
            max_submissions=parsed.max_submissions,
            cool_off_period=parsed.cool_off_period,
            amount_in_cool_off_period=parsed.amount_in_cool_off_period,
            ignore=parsed.ignore,
            ignore_version=parsed.ignore_version,
            done_type=parsed.done_type,
            reminder_time=parsed.reminder_time,
            done_email=parsed.done_email,
            anonymized_grading=parsed.anonymized_grading,
            file_to_load_first=parsed.file_to_load_first,
            grading=parsed.grading,
            grade_availability=parsed.grade_availability,
            submission_mode=parsed.submission_mode,
        )
        res.raw_data = d
        return res
