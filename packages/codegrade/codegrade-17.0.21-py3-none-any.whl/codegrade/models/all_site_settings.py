"""The module that defines the ``AllSiteSettings`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import datetime
import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing
from cg_maybe.utils import maybe_from_nullable

from ..utils import to_dict
from .frontend_site_settings import FrontendSiteSettings


@dataclass
class AllSiteSettings(FrontendSiteSettings):
    """The JSON representation of all options."""

    #: The amount of time there can be between two heartbeats of a runner.
    #: Changing this to a lower value might cause some runners to crash.
    auto_test_heartbeat_interval: Maybe[datetime.timedelta] = Nothing
    #: The max amount of heartbeats that we may miss from a runner before we
    #: kill it and start a new one.
    auto_test_heartbeat_max_missed: Maybe[int] = Nothing
    #: This value determines the amount of runners we request for a single
    #: assignment. The amount of runners requested is equal to the amount of
    #: students not yet started divided by this value.
    auto_test_max_jobs_per_runner: Maybe[int] = Nothing
    #: The maximum amount of batch AutoTest runs we will do at a time. AutoTest
    #: batch runs are runs that are done after the deadline for configurations
    #: that have hidden tests. Increasing this variable might cause heavy
    #: server load.
    auto_test_max_concurrent_batch_runs: Maybe[int] = Nothing
    #: The maximum amount of time a result can be in the "not started" state
    #: before we raise an alarm on the about health page.
    auto_test_max_result_not_started: Maybe[datetime.timedelta] = Nothing
    #: The maximum size of metadata stored on a unit test step.
    auto_test_max_unit_test_metadata_length: Maybe[int] = Nothing
    #: The maximum size of an AutoTest 2.0 configuration in the database.
    new_auto_test_max_dynamodb_size: Maybe[int] = Nothing
    #: The maximum compound size of all the files uploaded as part of an
    #: AutoTest 2.0 configuration.
    new_auto_test_max_storage_size: Maybe[int] = Nothing
    #: The maximum size of a single file part of an AutoTest 2.0 configuration.
    new_auto_test_max_file_size: Maybe[int] = Nothing
    #: The max output a command from a build step is allowed to output before
    #: output is truncated.
    new_auto_test_build_output_limit: Maybe[int] = Nothing
    #: The max output a command from a test step is allowed to output before
    #: output is truncated.
    new_auto_test_test_output_limit: Maybe[int] = Nothing
    #: The maximum combined file size of files uploaded in the Output step
    #: after compression.
    new_auto_test_max_output_files_size: Maybe[int] = Nothing
    #: The IDs of the available base images for AutoTest 2.0.
    new_auto_test_allowed_initial_build_ids: Maybe[t.Sequence[str]] = Nothing
    #: Unused, use `NEW_AUTO_TEST_CURRENT_INITIAL_BUILD_IDS`.
    new_auto_test_initial_build_id: Maybe[str] = Nothing
    #: The minimum strength passwords by users should have. The higher this
    #: value the stronger the password should be. When increasing the strength
    #: all users with too weak passwords will be shown a warning on the next
    #: login.
    min_password_score: Maybe[int] = Nothing
    #: The amount of time the link send in notification emails to change the
    #: notification preferences works to actually change the notifications.
    setting_token_time: Maybe[datetime.timedelta] = Nothing
    #: The maximum amount of files and directories allowed in a single archive.
    max_number_of_files: Maybe[int] = Nothing
    #: The maximum size of uploaded files that are mostly uploaded by "trusted"
    #: users. Examples of these kind of files include AutoTest fixtures and
    #: plagiarism base code.
    max_large_upload_size: Maybe[int] = Nothing
    #: The maximum total size of uploaded files that are uploaded by normal
    #: users. This is also the maximum total size of submissions. Increasing
    #: this size might cause a hosting costs to increase.
    max_normal_upload_size: Maybe[int] = Nothing
    #: The maximum total size of files part of an editor submission in
    #: dynamodb. This is not the same as `MAX_NORMAL_UPLOAD_SIZE`. Increasing
    #: this size might cause a hosting costs to increase.
    max_dynamo_submission_size: Maybe[int] = Nothing
    #: The maximum size of a single file uploaded by normal users. This limit
    #: is really here to prevent users from uploading extremely large files
    #: which can't really be downloaded/shown anyway.
    max_file_size: Maybe[int] = Nothing
    #: The maximum size of a single file's updates in dynamodb. This is not the
    #: same as `MAX_FILE_SIZE`. This limit is to avoid having huge files stored
    #: in dynamodb, as storage is expensive.
    max_dynamo_file_size: Maybe[int] = Nothing
    #: The maximum size of a single update (CRDT) to a file in dynamodb. This
    #: is not the same as `MAX_DYNAMO_FILE_SIZE`, as it refers to a single edit
    #: operation. This limit is to avoid having huge items stored in dynamodb,
    #: as storage is expensive. If the CRDT exceeds the given size, it will be
    #: uploaded to a S3 object.
    max_document_update_size: Maybe[int] = Nothing
    #: The time a login session is valid. After this amount of time a user will
    #: always need to re-authenticate.
    jwt_access_token_expires: Maybe[datetime.timedelta] = Nothing
    #: Whether username decollision - adding a number after the username if it
    #: already exists - should be enabled for SSO tenants.
    sso_username_decollision_enabled: Maybe[bool] = Nothing
    #: The maximum number of user settings stored per user.
    max_user_setting_amount: Maybe[int] = Nothing
    #: Should a registration email be sent to new users upon registration.
    send_registration_email: Maybe[bool] = Nothing
    #: Whether CodeGrade should try to automatically copy over assignment
    #: settings when it is detected that the course of an assignment is copied
    #: from another course within the same LTI provider.
    automatic_lti_1p3_assignment_import: Maybe[bool] = Nothing
    #: Wether to allow LTI to unset the deadline and lockdate of an assignment.
    lti_unset_deadline_lock_date_enabled: Maybe[bool] = Nothing
    #: Also look at context roles when determining the system role for a new
    #: user in LMSes that have an `extra_roles_mapping` defined in their
    #: `lms_capabilities`.
    lti_1p3_system_role_from_context_role: Maybe[bool] = Nothing
    #: Prefer the most privileged role in the LTI 1.3 roles claim sent by the
    #: LMS, instead of the first role that matches any of our definitions.
    lti_1p3_parse_most_privileged_role: Maybe[bool] = Nothing
    #: Enable logging of LTI launch data. NEVER ENABLE THIS SITE-WIDE, only for
    #: a single tenant, and disable this feature after you've gotten the data
    #: you need.
    lti_launch_data_logging: Maybe[bool] = Nothing
    #: Whether or not pearson templates should be enabled.
    pearson_templates: Maybe[bool] = Nothing
    #: The teacher role to be used for teachers in new courses. Existing
    #: courses will not be affected.
    default_course_teacher_role: Maybe[
        t.Literal["Full Teacher", "Non-Editing Teacher"]
    ] = Nothing
    #: The TA role to be used for TAs in new courses. Existing courses will not
    #: be affected.
    default_course_ta_role: Maybe[t.Literal["Full TA", "Non-Editing TA"]] = (
        Nothing
    )
    #: Whether LTI 1.3 launches using cookies (and sessions) should check for
    #: correct nonce and state. When disabling this feature flag, please be
    #: mindful. These validations protect us from certain attacks. If unsure,
    #: consult with the Security Officer before disabling.
    lti_1p3_nonce_and_state_validation_enabled: Maybe[bool] = Nothing
    #: Whether LTI 1.3 launches should check nonces against the cached value.
    #: Enabling this prevents replay attacks. If unsure, consult with the
    #: Security Officer before disabling.
    lti_1p3_prevent_nonce_reuse_enabled: Maybe[bool] = Nothing
    #: Do not store names and emails of users, but always retrieve them through
    #: NRPS.
    name_and_email_from_nrps_only: Maybe[bool] = Nothing
    #: Should we always update names and emails on LTI launches, or just when
    #: indicated and on the first launch.
    always_update_pii_with_lti: Maybe[bool] = Nothing
    #: Should we sync teachers to Hubspot.
    hubspot_syncing_enabled: Maybe[bool] = Nothing
    #: Whether we are running Codegrade for Pearson specifically, flag aligns
    #: all the smallest adjustments needed that cannot be made into an actual
    #: feature.
    is_pearson: Maybe[bool] = Nothing
    #: This enables if we change the role of a user in a course when a launch
    #: is done for a different role than the user currently has.
    lti_role_switching: Maybe[bool] = Nothing
    #: Controls whether users are also allowed to pay for courses individually.
    #: Tenant-wide access passes can always be used if available. If this
    #: setting is disabled, purchasing an access pass is the only way to pay
    #: for course access. If there are no tenant passes this setting has no
    #: influence.
    per_course_payment_allowed: Maybe[bool] = Nothing
    #: The payment provider to use for student payments. This should usually be
    #: configured at the tenant level, and will make new prices created in that
    #: tenant use this provider. Any existing prices and transactions will not
    #: be affected.
    payments_provider: Maybe[t.Literal["paddle", "stripe"]] = Nothing
    #: Whether to recalculate the rubric scores from the ATv2 results when
    #: converting a discrete row to a continuous one.
    rubric_convert_use_atv2_enabled: Maybe[bool] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: FrontendSiteSettings.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.OptionalArgument(
                    "AUTO_TEST_HEARTBEAT_INTERVAL",
                    rqa.RichValue.TimeDelta,
                    doc="The amount of time there can be between two heartbeats of a runner. Changing this to a lower value might cause some runners to crash.",
                ),
                rqa.OptionalArgument(
                    "AUTO_TEST_HEARTBEAT_MAX_MISSED",
                    rqa.SimpleValue.int,
                    doc="The max amount of heartbeats that we may miss from a runner before we kill it and start a new one.",
                ),
                rqa.OptionalArgument(
                    "AUTO_TEST_MAX_JOBS_PER_RUNNER",
                    rqa.SimpleValue.int,
                    doc="This value determines the amount of runners we request for a single assignment. The amount of runners requested is equal to the amount of students not yet started divided by this value.",
                ),
                rqa.OptionalArgument(
                    "AUTO_TEST_MAX_CONCURRENT_BATCH_RUNS",
                    rqa.SimpleValue.int,
                    doc="The maximum amount of batch AutoTest runs we will do at a time. AutoTest batch runs are runs that are done after the deadline for configurations that have hidden tests. Increasing this variable might cause heavy server load.",
                ),
                rqa.OptionalArgument(
                    "AUTO_TEST_MAX_RESULT_NOT_STARTED",
                    rqa.RichValue.TimeDelta,
                    doc='The maximum amount of time a result can be in the "not started" state before we raise an alarm on the about health page.',
                ),
                rqa.OptionalArgument(
                    "AUTO_TEST_MAX_UNIT_TEST_METADATA_LENGTH",
                    rqa.SimpleValue.int,
                    doc="The maximum size of metadata stored on a unit test step.",
                ),
                rqa.OptionalArgument(
                    "NEW_AUTO_TEST_MAX_DYNAMODB_SIZE",
                    rqa.SimpleValue.int,
                    doc="The maximum size of an AutoTest 2.0 configuration in the database.",
                ),
                rqa.OptionalArgument(
                    "NEW_AUTO_TEST_MAX_STORAGE_SIZE",
                    rqa.SimpleValue.int,
                    doc="The maximum compound size of all the files uploaded as part of an AutoTest 2.0 configuration.",
                ),
                rqa.OptionalArgument(
                    "NEW_AUTO_TEST_MAX_FILE_SIZE",
                    rqa.SimpleValue.int,
                    doc="The maximum size of a single file part of an AutoTest 2.0 configuration.",
                ),
                rqa.OptionalArgument(
                    "NEW_AUTO_TEST_BUILD_OUTPUT_LIMIT",
                    rqa.SimpleValue.int,
                    doc="The max output a command from a build step is allowed to output before output is truncated.",
                ),
                rqa.OptionalArgument(
                    "NEW_AUTO_TEST_TEST_OUTPUT_LIMIT",
                    rqa.SimpleValue.int,
                    doc="The max output a command from a test step is allowed to output before output is truncated.",
                ),
                rqa.OptionalArgument(
                    "NEW_AUTO_TEST_MAX_OUTPUT_FILES_SIZE",
                    rqa.SimpleValue.int,
                    doc="The maximum combined file size of files uploaded in the Output step after compression.",
                ),
                rqa.OptionalArgument(
                    "NEW_AUTO_TEST_ALLOWED_INITIAL_BUILD_IDS",
                    rqa.List(rqa.SimpleValue.str),
                    doc="The IDs of the available base images for AutoTest 2.0.",
                ),
                rqa.OptionalArgument(
                    "NEW_AUTO_TEST_INITIAL_BUILD_ID",
                    rqa.SimpleValue.str,
                    doc="Unused, use `NEW_AUTO_TEST_CURRENT_INITIAL_BUILD_IDS`.",
                ),
                rqa.OptionalArgument(
                    "MIN_PASSWORD_SCORE",
                    rqa.SimpleValue.int,
                    doc="The minimum strength passwords by users should have. The higher this value the stronger the password should be. When increasing the strength all users with too weak passwords will be shown a warning on the next login.",
                ),
                rqa.OptionalArgument(
                    "SETTING_TOKEN_TIME",
                    rqa.RichValue.TimeDelta,
                    doc="The amount of time the link send in notification emails to change the notification preferences works to actually change the notifications.",
                ),
                rqa.OptionalArgument(
                    "MAX_NUMBER_OF_FILES",
                    rqa.SimpleValue.int,
                    doc="The maximum amount of files and directories allowed in a single archive.",
                ),
                rqa.OptionalArgument(
                    "MAX_LARGE_UPLOAD_SIZE",
                    rqa.SimpleValue.int,
                    doc='The maximum size of uploaded files that are mostly uploaded by "trusted" users. Examples of these kind of files include AutoTest fixtures and plagiarism base code.',
                ),
                rqa.OptionalArgument(
                    "MAX_NORMAL_UPLOAD_SIZE",
                    rqa.SimpleValue.int,
                    doc="The maximum total size of uploaded files that are uploaded by normal users. This is also the maximum total size of submissions. Increasing this size might cause a hosting costs to increase.",
                ),
                rqa.OptionalArgument(
                    "MAX_DYNAMO_SUBMISSION_SIZE",
                    rqa.SimpleValue.int,
                    doc="The maximum total size of files part of an editor submission in dynamodb. This is not the same as `MAX_NORMAL_UPLOAD_SIZE`. Increasing this size might cause a hosting costs to increase.",
                ),
                rqa.OptionalArgument(
                    "MAX_FILE_SIZE",
                    rqa.SimpleValue.int,
                    doc="The maximum size of a single file uploaded by normal users. This limit is really here to prevent users from uploading extremely large files which can't really be downloaded/shown anyway.",
                ),
                rqa.OptionalArgument(
                    "MAX_DYNAMO_FILE_SIZE",
                    rqa.SimpleValue.int,
                    doc="The maximum size of a single file's updates in dynamodb. This is not the same as `MAX_FILE_SIZE`. This limit is to avoid having huge files stored in dynamodb, as storage is expensive.",
                ),
                rqa.OptionalArgument(
                    "MAX_DOCUMENT_UPDATE_SIZE",
                    rqa.SimpleValue.int,
                    doc="The maximum size of a single update (CRDT) to a file in dynamodb. This is not the same as `MAX_DYNAMO_FILE_SIZE`, as it refers to a single edit operation. This limit is to avoid having huge items stored in dynamodb, as storage is expensive. If the CRDT exceeds the given size, it will be uploaded to a S3 object.",
                ),
                rqa.OptionalArgument(
                    "JWT_ACCESS_TOKEN_EXPIRES",
                    rqa.RichValue.TimeDelta,
                    doc="The time a login session is valid. After this amount of time a user will always need to re-authenticate.",
                ),
                rqa.OptionalArgument(
                    "SSO_USERNAME_DECOLLISION_ENABLED",
                    rqa.SimpleValue.bool,
                    doc="Whether username decollision - adding a number after the username if it already exists - should be enabled for SSO tenants.",
                ),
                rqa.OptionalArgument(
                    "MAX_USER_SETTING_AMOUNT",
                    rqa.SimpleValue.int,
                    doc="The maximum number of user settings stored per user.",
                ),
                rqa.OptionalArgument(
                    "SEND_REGISTRATION_EMAIL",
                    rqa.SimpleValue.bool,
                    doc="Should a registration email be sent to new users upon registration.",
                ),
                rqa.OptionalArgument(
                    "AUTOMATIC_LTI_1P3_ASSIGNMENT_IMPORT",
                    rqa.SimpleValue.bool,
                    doc="Whether CodeGrade should try to automatically copy over assignment settings when it is detected that the course of an assignment is copied from another course within the same LTI provider.",
                ),
                rqa.OptionalArgument(
                    "LTI_UNSET_DEADLINE_LOCK_DATE_ENABLED",
                    rqa.SimpleValue.bool,
                    doc="Wether to allow LTI to unset the deadline and lockdate of an assignment.",
                ),
                rqa.OptionalArgument(
                    "LTI_1P3_SYSTEM_ROLE_FROM_CONTEXT_ROLE",
                    rqa.SimpleValue.bool,
                    doc="Also look at context roles when determining the system role for a new user in LMSes that have an `extra_roles_mapping` defined in their `lms_capabilities`.",
                ),
                rqa.OptionalArgument(
                    "LTI_1P3_PARSE_MOST_PRIVILEGED_ROLE",
                    rqa.SimpleValue.bool,
                    doc="Prefer the most privileged role in the LTI 1.3 roles claim sent by the LMS, instead of the first role that matches any of our definitions.",
                ),
                rqa.OptionalArgument(
                    "LTI_LAUNCH_DATA_LOGGING",
                    rqa.SimpleValue.bool,
                    doc="Enable logging of LTI launch data. NEVER ENABLE THIS SITE-WIDE, only for a single tenant, and disable this feature after you've gotten the data you need.",
                ),
                rqa.OptionalArgument(
                    "PEARSON_TEMPLATES",
                    rqa.SimpleValue.bool,
                    doc="Whether or not pearson templates should be enabled.",
                ),
                rqa.OptionalArgument(
                    "DEFAULT_COURSE_TEACHER_ROLE",
                    rqa.StringEnum("Full Teacher", "Non-Editing Teacher"),
                    doc="The teacher role to be used for teachers in new courses. Existing courses will not be affected.",
                ),
                rqa.OptionalArgument(
                    "DEFAULT_COURSE_TA_ROLE",
                    rqa.StringEnum("Full TA", "Non-Editing TA"),
                    doc="The TA role to be used for TAs in new courses. Existing courses will not be affected.",
                ),
                rqa.OptionalArgument(
                    "LTI_1P3_NONCE_AND_STATE_VALIDATION_ENABLED",
                    rqa.SimpleValue.bool,
                    doc="Whether LTI 1.3 launches using cookies (and sessions) should check for correct nonce and state. When disabling this feature flag, please be mindful. These validations protect us from certain attacks. If unsure, consult with the Security Officer before disabling.",
                ),
                rqa.OptionalArgument(
                    "LTI_1P3_PREVENT_NONCE_REUSE_ENABLED",
                    rqa.SimpleValue.bool,
                    doc="Whether LTI 1.3 launches should check nonces against the cached value. Enabling this prevents replay attacks. If unsure, consult with the Security Officer before disabling.",
                ),
                rqa.OptionalArgument(
                    "NAME_AND_EMAIL_FROM_NRPS_ONLY",
                    rqa.SimpleValue.bool,
                    doc="Do not store names and emails of users, but always retrieve them through NRPS.",
                ),
                rqa.OptionalArgument(
                    "ALWAYS_UPDATE_PII_WITH_LTI",
                    rqa.SimpleValue.bool,
                    doc="Should we always update names and emails on LTI launches, or just when indicated and on the first launch.",
                ),
                rqa.OptionalArgument(
                    "HUBSPOT_SYNCING_ENABLED",
                    rqa.SimpleValue.bool,
                    doc="Should we sync teachers to Hubspot.",
                ),
                rqa.OptionalArgument(
                    "IS_PEARSON",
                    rqa.SimpleValue.bool,
                    doc="Whether we are running Codegrade for Pearson specifically, flag aligns all the smallest adjustments needed that cannot be made into an actual feature.",
                ),
                rqa.OptionalArgument(
                    "LTI_ROLE_SWITCHING",
                    rqa.SimpleValue.bool,
                    doc="This enables if we change the role of a user in a course when a launch is done for a different role than the user currently has.",
                ),
                rqa.OptionalArgument(
                    "PER_COURSE_PAYMENT_ALLOWED",
                    rqa.SimpleValue.bool,
                    doc="Controls whether users are also allowed to pay for courses individually. Tenant-wide access passes can always be used if available. If this setting is disabled, purchasing an access pass is the only way to pay for course access. If there are no tenant passes this setting has no influence.",
                ),
                rqa.OptionalArgument(
                    "PAYMENTS_PROVIDER",
                    rqa.StringEnum("paddle", "stripe"),
                    doc="The payment provider to use for student payments. This should usually be configured at the tenant level, and will make new prices created in that tenant use this provider. Any existing prices and transactions will not be affected.",
                ),
                rqa.OptionalArgument(
                    "RUBRIC_CONVERT_USE_ATV2_ENABLED",
                    rqa.SimpleValue.bool,
                    doc="Whether to recalculate the rubric scores from the ATv2 results when converting a discrete row to a continuous one.",
                ),
            )
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.auto_test_heartbeat_interval = maybe_from_nullable(
            self.auto_test_heartbeat_interval
        )
        self.auto_test_heartbeat_max_missed = maybe_from_nullable(
            self.auto_test_heartbeat_max_missed
        )
        self.auto_test_max_jobs_per_runner = maybe_from_nullable(
            self.auto_test_max_jobs_per_runner
        )
        self.auto_test_max_concurrent_batch_runs = maybe_from_nullable(
            self.auto_test_max_concurrent_batch_runs
        )
        self.auto_test_max_result_not_started = maybe_from_nullable(
            self.auto_test_max_result_not_started
        )
        self.auto_test_max_unit_test_metadata_length = maybe_from_nullable(
            self.auto_test_max_unit_test_metadata_length
        )
        self.new_auto_test_max_dynamodb_size = maybe_from_nullable(
            self.new_auto_test_max_dynamodb_size
        )
        self.new_auto_test_max_storage_size = maybe_from_nullable(
            self.new_auto_test_max_storage_size
        )
        self.new_auto_test_max_file_size = maybe_from_nullable(
            self.new_auto_test_max_file_size
        )
        self.new_auto_test_build_output_limit = maybe_from_nullable(
            self.new_auto_test_build_output_limit
        )
        self.new_auto_test_test_output_limit = maybe_from_nullable(
            self.new_auto_test_test_output_limit
        )
        self.new_auto_test_max_output_files_size = maybe_from_nullable(
            self.new_auto_test_max_output_files_size
        )
        self.new_auto_test_allowed_initial_build_ids = maybe_from_nullable(
            self.new_auto_test_allowed_initial_build_ids
        )
        self.new_auto_test_initial_build_id = maybe_from_nullable(
            self.new_auto_test_initial_build_id
        )
        self.min_password_score = maybe_from_nullable(self.min_password_score)
        self.setting_token_time = maybe_from_nullable(self.setting_token_time)
        self.max_number_of_files = maybe_from_nullable(
            self.max_number_of_files
        )
        self.max_large_upload_size = maybe_from_nullable(
            self.max_large_upload_size
        )
        self.max_normal_upload_size = maybe_from_nullable(
            self.max_normal_upload_size
        )
        self.max_dynamo_submission_size = maybe_from_nullable(
            self.max_dynamo_submission_size
        )
        self.max_file_size = maybe_from_nullable(self.max_file_size)
        self.max_dynamo_file_size = maybe_from_nullable(
            self.max_dynamo_file_size
        )
        self.max_document_update_size = maybe_from_nullable(
            self.max_document_update_size
        )
        self.jwt_access_token_expires = maybe_from_nullable(
            self.jwt_access_token_expires
        )
        self.sso_username_decollision_enabled = maybe_from_nullable(
            self.sso_username_decollision_enabled
        )
        self.max_user_setting_amount = maybe_from_nullable(
            self.max_user_setting_amount
        )
        self.send_registration_email = maybe_from_nullable(
            self.send_registration_email
        )
        self.automatic_lti_1p3_assignment_import = maybe_from_nullable(
            self.automatic_lti_1p3_assignment_import
        )
        self.lti_unset_deadline_lock_date_enabled = maybe_from_nullable(
            self.lti_unset_deadline_lock_date_enabled
        )
        self.lti_1p3_system_role_from_context_role = maybe_from_nullable(
            self.lti_1p3_system_role_from_context_role
        )
        self.lti_1p3_parse_most_privileged_role = maybe_from_nullable(
            self.lti_1p3_parse_most_privileged_role
        )
        self.lti_launch_data_logging = maybe_from_nullable(
            self.lti_launch_data_logging
        )
        self.pearson_templates = maybe_from_nullable(self.pearson_templates)
        self.default_course_teacher_role = maybe_from_nullable(
            self.default_course_teacher_role
        )
        self.default_course_ta_role = maybe_from_nullable(
            self.default_course_ta_role
        )
        self.lti_1p3_nonce_and_state_validation_enabled = maybe_from_nullable(
            self.lti_1p3_nonce_and_state_validation_enabled
        )
        self.lti_1p3_prevent_nonce_reuse_enabled = maybe_from_nullable(
            self.lti_1p3_prevent_nonce_reuse_enabled
        )
        self.name_and_email_from_nrps_only = maybe_from_nullable(
            self.name_and_email_from_nrps_only
        )
        self.always_update_pii_with_lti = maybe_from_nullable(
            self.always_update_pii_with_lti
        )
        self.hubspot_syncing_enabled = maybe_from_nullable(
            self.hubspot_syncing_enabled
        )
        self.is_pearson = maybe_from_nullable(self.is_pearson)
        self.lti_role_switching = maybe_from_nullable(self.lti_role_switching)
        self.per_course_payment_allowed = maybe_from_nullable(
            self.per_course_payment_allowed
        )
        self.payments_provider = maybe_from_nullable(self.payments_provider)
        self.rubric_convert_use_atv2_enabled = maybe_from_nullable(
            self.rubric_convert_use_atv2_enabled
        )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {}
        if self.auto_test_max_time_command.is_just:
            res["AUTO_TEST_MAX_TIME_COMMAND"] = to_dict(
                self.auto_test_max_time_command.value
            )
        if self.auto_test_io_test_message.is_just:
            res["AUTO_TEST_IO_TEST_MESSAGE"] = to_dict(
                self.auto_test_io_test_message.value
            )
        if self.auto_test_io_test_sub_message.is_just:
            res["AUTO_TEST_IO_TEST_SUB_MESSAGE"] = to_dict(
                self.auto_test_io_test_sub_message.value
            )
        if self.auto_test_run_program_message.is_just:
            res["AUTO_TEST_RUN_PROGRAM_MESSAGE"] = to_dict(
                self.auto_test_run_program_message.value
            )
        if self.auto_test_capture_points_message.is_just:
            res["AUTO_TEST_CAPTURE_POINTS_MESSAGE"] = to_dict(
                self.auto_test_capture_points_message.value
            )
        if self.auto_test_checkpoint_message.is_just:
            res["AUTO_TEST_CHECKPOINT_MESSAGE"] = to_dict(
                self.auto_test_checkpoint_message.value
            )
        if self.auto_test_unit_test_message.is_just:
            res["AUTO_TEST_UNIT_TEST_MESSAGE"] = to_dict(
                self.auto_test_unit_test_message.value
            )
        if self.auto_test_code_quality_message.is_just:
            res["AUTO_TEST_CODE_QUALITY_MESSAGE"] = to_dict(
                self.auto_test_code_quality_message.value
            )
        if self.new_auto_test_current_initial_build_ids.is_just:
            res["NEW_AUTO_TEST_CURRENT_INITIAL_BUILD_IDS"] = to_dict(
                self.new_auto_test_current_initial_build_ids.value
            )
        if self.new_auto_test_build_max_command_time.is_just:
            res["NEW_AUTO_TEST_BUILD_MAX_COMMAND_TIME"] = to_dict(
                self.new_auto_test_build_max_command_time.value
            )
        if self.new_auto_test_test_max_command_time.is_just:
            res["NEW_AUTO_TEST_TEST_MAX_COMMAND_TIME"] = to_dict(
                self.new_auto_test_test_max_command_time.value
            )
        if self.code_editor_output_viewer_title.is_just:
            res["CODE_EDITOR_OUTPUT_VIEWER_TITLE"] = to_dict(
                self.code_editor_output_viewer_title.value
            )
        if self.exam_login_max_length.is_just:
            res["EXAM_LOGIN_MAX_LENGTH"] = to_dict(
                self.exam_login_max_length.value
            )
        if self.login_token_before_time.is_just:
            res["LOGIN_TOKEN_BEFORE_TIME"] = to_dict(
                self.login_token_before_time.value
            )
        if self.reset_token_time.is_just:
            res["RESET_TOKEN_TIME"] = to_dict(self.reset_token_time.value)
        if self.site_email.is_just:
            res["SITE_EMAIL"] = to_dict(self.site_email.value)
        if self.access_token_toast_warning_time.is_just:
            res["ACCESS_TOKEN_TOAST_WARNING_TIME"] = to_dict(
                self.access_token_toast_warning_time.value
            )
        if self.access_token_modal_warning_time.is_just:
            res["ACCESS_TOKEN_MODAL_WARNING_TIME"] = to_dict(
                self.access_token_modal_warning_time.value
            )
        if self.max_lines.is_just:
            res["MAX_LINES"] = to_dict(self.max_lines.value)
        if self.notification_poll_time.is_just:
            res["NOTIFICATION_POLL_TIME"] = to_dict(
                self.notification_poll_time.value
            )
        if self.release_message_max_time.is_just:
            res["RELEASE_MESSAGE_MAX_TIME"] = to_dict(
                self.release_message_max_time.value
            )
        if self.max_plagiarism_matches.is_just:
            res["MAX_PLAGIARISM_MATCHES"] = to_dict(
                self.max_plagiarism_matches.value
            )
        if self.auto_test_max_global_setup_time.is_just:
            res["AUTO_TEST_MAX_GLOBAL_SETUP_TIME"] = to_dict(
                self.auto_test_max_global_setup_time.value
            )
        if self.auto_test_max_per_student_setup_time.is_just:
            res["AUTO_TEST_MAX_PER_STUDENT_SETUP_TIME"] = to_dict(
                self.auto_test_max_per_student_setup_time.value
            )
        if self.assignment_default_grading_scale.is_just:
            res["ASSIGNMENT_DEFAULT_GRADING_SCALE"] = to_dict(
                self.assignment_default_grading_scale.value
            )
        if self.assignment_default_grading_scale_points.is_just:
            res["ASSIGNMENT_DEFAULT_GRADING_SCALE_POINTS"] = to_dict(
                self.assignment_default_grading_scale_points.value
            )
        if self.blackboard_zip_upload_enabled.is_just:
            res["BLACKBOARD_ZIP_UPLOAD_ENABLED"] = to_dict(
                self.blackboard_zip_upload_enabled.value
            )
        if self.rubric_enabled_for_teacher_on_submissions_page.is_just:
            res["RUBRIC_ENABLED_FOR_TEACHER_ON_SUBMISSIONS_PAGE"] = to_dict(
                self.rubric_enabled_for_teacher_on_submissions_page.value
            )
        if self.automatic_lti_role_enabled.is_just:
            res["AUTOMATIC_LTI_ROLE_ENABLED"] = to_dict(
                self.automatic_lti_role_enabled.value
            )
        if self.register_enabled.is_just:
            res["REGISTER_ENABLED"] = to_dict(self.register_enabled.value)
        if self.groups_enabled.is_just:
            res["GROUPS_ENABLED"] = to_dict(self.groups_enabled.value)
        if self.auto_test_enabled.is_just:
            res["AUTO_TEST_ENABLED"] = to_dict(self.auto_test_enabled.value)
        if self.course_register_enabled.is_just:
            res["COURSE_REGISTER_ENABLED"] = to_dict(
                self.course_register_enabled.value
            )
        if self.render_html_enabled.is_just:
            res["RENDER_HTML_ENABLED"] = to_dict(
                self.render_html_enabled.value
            )
        if self.email_students_enabled.is_just:
            res["EMAIL_STUDENTS_ENABLED"] = to_dict(
                self.email_students_enabled.value
            )
        if self.peer_feedback_enabled.is_just:
            res["PEER_FEEDBACK_ENABLED"] = to_dict(
                self.peer_feedback_enabled.value
            )
        if self.at_image_caching_enabled.is_just:
            res["AT_IMAGE_CACHING_ENABLED"] = to_dict(
                self.at_image_caching_enabled.value
            )
        if self.student_payment_enabled.is_just:
            res["STUDENT_PAYMENT_ENABLED"] = to_dict(
                self.student_payment_enabled.value
            )
        if self.student_payment_main_option.is_just:
            res["STUDENT_PAYMENT_MAIN_OPTION"] = to_dict(
                self.student_payment_main_option.value
            )
        if self.editor_enabled.is_just:
            res["EDITOR_ENABLED"] = to_dict(self.editor_enabled.value)
        if self.server_time_correction_enabled.is_just:
            res["SERVER_TIME_CORRECTION_ENABLED"] = to_dict(
                self.server_time_correction_enabled.value
            )
        if self.grading_notifications_enabled.is_just:
            res["GRADING_NOTIFICATIONS_ENABLED"] = to_dict(
                self.grading_notifications_enabled.value
            )
        if self.feedback_threads_initially_collapsed.is_just:
            res["FEEDBACK_THREADS_INITIALLY_COLLAPSED"] = to_dict(
                self.feedback_threads_initially_collapsed.value
            )
        if self.server_time_diff_tolerance.is_just:
            res["SERVER_TIME_DIFF_TOLERANCE"] = to_dict(
                self.server_time_diff_tolerance.value
            )
        if self.server_time_sync_interval.is_just:
            res["SERVER_TIME_SYNC_INTERVAL"] = to_dict(
                self.server_time_sync_interval.value
            )
        if self.assignment_percentage_decimals.is_just:
            res["ASSIGNMENT_PERCENTAGE_DECIMALS"] = to_dict(
                self.assignment_percentage_decimals.value
            )
        if self.assignment_point_decimals.is_just:
            res["ASSIGNMENT_POINT_DECIMALS"] = to_dict(
                self.assignment_point_decimals.value
            )
        if self.output_viewer_animation_limit_lines_count.is_just:
            res["OUTPUT_VIEWER_ANIMATION_LIMIT_LINES_COUNT"] = to_dict(
                self.output_viewer_animation_limit_lines_count.value
            )
        if self.output_viewer_auto_expand_failed_steps.is_just:
            res["OUTPUT_VIEWER_AUTO_EXPAND_FAILED_STEPS"] = to_dict(
                self.output_viewer_auto_expand_failed_steps.value
            )
        if self.lti_lock_date_copying_enabled.is_just:
            res["LTI_LOCK_DATE_COPYING_ENABLED"] = to_dict(
                self.lti_lock_date_copying_enabled.value
            )
        if self.assignment_max_points_enabled.is_just:
            res["ASSIGNMENT_MAX_POINTS_ENABLED"] = to_dict(
                self.assignment_max_points_enabled.value
            )
        if self.course_gradebook_render_warning_size.is_just:
            res["COURSE_GRADEBOOK_RENDER_WARNING_SIZE"] = to_dict(
                self.course_gradebook_render_warning_size.value
            )
        if self.course_bulk_register_enabled.is_just:
            res["COURSE_BULK_REGISTER_ENABLED"] = to_dict(
                self.course_bulk_register_enabled.value
            )
        if self.csv_large_file_limit.is_just:
            res["CSV_LARGE_FILE_LIMIT"] = to_dict(
                self.csv_large_file_limit.value
            )
        if self.csv_too_many_errors_limit.is_just:
            res["CSV_TOO_MANY_ERRORS_LIMIT"] = to_dict(
                self.csv_too_many_errors_limit.value
            )
        if self.new_auto_test_old_submission_age.is_just:
            res["NEW_AUTO_TEST_OLD_SUBMISSION_AGE"] = to_dict(
                self.new_auto_test_old_submission_age.value
            )
        if self.canvas_course_id_copying_enabled.is_just:
            res["CANVAS_COURSE_ID_COPYING_ENABLED"] = to_dict(
                self.canvas_course_id_copying_enabled.value
            )
        if self.new_auto_test_diff_viewer_enabled.is_just:
            res["NEW_AUTO_TEST_DIFF_VIEWER_ENABLED"] = to_dict(
                self.new_auto_test_diff_viewer_enabled.value
            )
        if self.github_template_repo_enabled.is_just:
            res["GITHUB_TEMPLATE_REPO_ENABLED"] = to_dict(
                self.github_template_repo_enabled.value
            )
        if self.community_library.is_just:
            res["COMMUNITY_LIBRARY"] = to_dict(self.community_library.value)
        if self.community_library_publishing.is_just:
            res["COMMUNITY_LIBRARY_PUBLISHING"] = to_dict(
                self.community_library_publishing.value
            )
        if self.quality_comments_in_code_editor.is_just:
            res["QUALITY_COMMENTS_IN_CODE_EDITOR"] = to_dict(
                self.quality_comments_in_code_editor.value
            )
        if self.sso_infer_global_staff_role.is_just:
            res["SSO_INFER_GLOBAL_STAFF_ROLE"] = to_dict(
                self.sso_infer_global_staff_role.value
            )
        if self.new_auto_test_uncollapsing_step_output_delay.is_just:
            res["NEW_AUTO_TEST_UNCOLLAPSING_STEP_OUTPUT_DELAY"] = to_dict(
                self.new_auto_test_uncollapsing_step_output_delay.value
            )
        if self.assignment_description_on_teachers_submissions_page.is_just:
            res["ASSIGNMENT_DESCRIPTION_ON_TEACHERS_SUBMISSIONS_PAGE"] = (
                to_dict(
                    self.assignment_description_on_teachers_submissions_page.value
                )
            )
        if self.inline_rubric_viewer_enabled.is_just:
            res["INLINE_RUBRIC_VIEWER_ENABLED"] = to_dict(
                self.inline_rubric_viewer_enabled.value
            )
        if self.hide_code_editor_output_viewer_with_only_quiz_steps.is_just:
            res["HIDE_CODE_EDITOR_OUTPUT_VIEWER_WITH_ONLY_QUIZ_STEPS"] = (
                to_dict(
                    self.hide_code_editor_output_viewer_with_only_quiz_steps.value
                )
            )
        if self.hide_code_editor_filetree_controls_with_only_quiz_steps.is_just:
            res["HIDE_CODE_EDITOR_FILETREE_CONTROLS_WITH_ONLY_QUIZ_STEPS"] = (
                to_dict(
                    self.hide_code_editor_filetree_controls_with_only_quiz_steps.value
                )
            )
        if self.simple_submission_navigate_to_latest_editor_session.is_just:
            res["SIMPLE_SUBMISSION_NAVIGATE_TO_LATEST_EDITOR_SESSION"] = (
                to_dict(
                    self.simple_submission_navigate_to_latest_editor_session.value
                )
            )
        if self.display_grades_enabled.is_just:
            res["DISPLAY_GRADES_ENABLED"] = to_dict(
                self.display_grades_enabled.value
            )
        if self.hide_empty_rubric_row_description.is_just:
            res["HIDE_EMPTY_RUBRIC_ROW_DESCRIPTION"] = to_dict(
                self.hide_empty_rubric_row_description.value
            )
        if self.default_submission_page_tab.is_just:
            res["DEFAULT_SUBMISSION_PAGE_TAB"] = to_dict(
                self.default_submission_page_tab.value
            )
        if self.hide_no_deadline_enabled.is_just:
            res["HIDE_NO_DEADLINE_ENABLED"] = to_dict(
                self.hide_no_deadline_enabled.value
            )
        if self.retry_group_submission_grade_passback_enabled.is_just:
            res["RETRY_GROUP_SUBMISSION_GRADE_PASSBACK_ENABLED"] = to_dict(
                self.retry_group_submission_grade_passback_enabled.value
            )
        if self.code_editor_start_on_assignment_description.is_just:
            res["CODE_EDITOR_START_ON_ASSIGNMENT_DESCRIPTION"] = to_dict(
                self.code_editor_start_on_assignment_description.value
            )
        if self.ai_assistant_enabled.is_just:
            res["AI_ASSISTANT_ENABLED"] = to_dict(
                self.ai_assistant_enabled.value
            )
        if self.assistant_tools_enabled.is_just:
            res["ASSISTANT_TOOLS_ENABLED"] = to_dict(
                self.assistant_tools_enabled.value
            )
        if self.prompt_engineering_step_enabled.is_just:
            res["PROMPT_ENGINEERING_STEP_ENABLED"] = to_dict(
                self.prompt_engineering_step_enabled.value
            )
        if self.first_day_of_week_from_locale.is_just:
            res["FIRST_DAY_OF_WEEK_FROM_LOCALE"] = to_dict(
                self.first_day_of_week_from_locale.value
            )
        if self.inline_feedback_on_quizzes_enabled.is_just:
            res["INLINE_FEEDBACK_ON_QUIZZES_ENABLED"] = to_dict(
                self.inline_feedback_on_quizzes_enabled.value
            )
        if self.quiz_single_question_mode_hide_run_button_enabled.is_just:
            res["QUIZ_SINGLE_QUESTION_MODE_HIDE_RUN_BUTTON_ENABLED"] = to_dict(
                self.quiz_single_question_mode_hide_run_button_enabled.value
            )
        if self.warning_for_missing_newline_enabled.is_just:
            res["WARNING_FOR_MISSING_NEWLINE_ENABLED"] = to_dict(
                self.warning_for_missing_newline_enabled.value
            )
        if self.jupyter_notebook_editor_enabled.is_just:
            res["JUPYTER_NOTEBOOK_EDITOR_ENABLED"] = to_dict(
                self.jupyter_notebook_editor_enabled.value
            )
        if self.jupyter_notebook_running_enabled.is_just:
            res["JUPYTER_NOTEBOOK_RUNNING_ENABLED"] = to_dict(
                self.jupyter_notebook_running_enabled.value
            )
        if self.coding_question_editor_reset_answer_enabled.is_just:
            res["CODING_QUESTION_EDITOR_RESET_ANSWER_ENABLED"] = to_dict(
                self.coding_question_editor_reset_answer_enabled.value
            )
        if self.coding_question_solution_enabled.is_just:
            res["CODING_QUESTION_SOLUTION_ENABLED"] = to_dict(
                self.coding_question_solution_enabled.value
            )
        if self.download_editor_files_enabled.is_just:
            res["DOWNLOAD_EDITOR_FILES_ENABLED"] = to_dict(
                self.download_editor_files_enabled.value
            )
        if self.quiz_view_modes_enabled.is_just:
            res["QUIZ_VIEW_MODES_ENABLED"] = to_dict(
                self.quiz_view_modes_enabled.value
            )
        if self.regex_atv2_explanation_enabled.is_just:
            res["REGEX_ATV2_EXPLANATION_ENABLED"] = to_dict(
                self.regex_atv2_explanation_enabled.value
            )
        if self.auto_test_heartbeat_interval.is_just:
            res["AUTO_TEST_HEARTBEAT_INTERVAL"] = to_dict(
                self.auto_test_heartbeat_interval.value
            )
        if self.auto_test_heartbeat_max_missed.is_just:
            res["AUTO_TEST_HEARTBEAT_MAX_MISSED"] = to_dict(
                self.auto_test_heartbeat_max_missed.value
            )
        if self.auto_test_max_jobs_per_runner.is_just:
            res["AUTO_TEST_MAX_JOBS_PER_RUNNER"] = to_dict(
                self.auto_test_max_jobs_per_runner.value
            )
        if self.auto_test_max_concurrent_batch_runs.is_just:
            res["AUTO_TEST_MAX_CONCURRENT_BATCH_RUNS"] = to_dict(
                self.auto_test_max_concurrent_batch_runs.value
            )
        if self.auto_test_max_result_not_started.is_just:
            res["AUTO_TEST_MAX_RESULT_NOT_STARTED"] = to_dict(
                self.auto_test_max_result_not_started.value
            )
        if self.auto_test_max_unit_test_metadata_length.is_just:
            res["AUTO_TEST_MAX_UNIT_TEST_METADATA_LENGTH"] = to_dict(
                self.auto_test_max_unit_test_metadata_length.value
            )
        if self.new_auto_test_max_dynamodb_size.is_just:
            res["NEW_AUTO_TEST_MAX_DYNAMODB_SIZE"] = to_dict(
                self.new_auto_test_max_dynamodb_size.value
            )
        if self.new_auto_test_max_storage_size.is_just:
            res["NEW_AUTO_TEST_MAX_STORAGE_SIZE"] = to_dict(
                self.new_auto_test_max_storage_size.value
            )
        if self.new_auto_test_max_file_size.is_just:
            res["NEW_AUTO_TEST_MAX_FILE_SIZE"] = to_dict(
                self.new_auto_test_max_file_size.value
            )
        if self.new_auto_test_build_output_limit.is_just:
            res["NEW_AUTO_TEST_BUILD_OUTPUT_LIMIT"] = to_dict(
                self.new_auto_test_build_output_limit.value
            )
        if self.new_auto_test_test_output_limit.is_just:
            res["NEW_AUTO_TEST_TEST_OUTPUT_LIMIT"] = to_dict(
                self.new_auto_test_test_output_limit.value
            )
        if self.new_auto_test_max_output_files_size.is_just:
            res["NEW_AUTO_TEST_MAX_OUTPUT_FILES_SIZE"] = to_dict(
                self.new_auto_test_max_output_files_size.value
            )
        if self.new_auto_test_allowed_initial_build_ids.is_just:
            res["NEW_AUTO_TEST_ALLOWED_INITIAL_BUILD_IDS"] = to_dict(
                self.new_auto_test_allowed_initial_build_ids.value
            )
        if self.new_auto_test_initial_build_id.is_just:
            res["NEW_AUTO_TEST_INITIAL_BUILD_ID"] = to_dict(
                self.new_auto_test_initial_build_id.value
            )
        if self.min_password_score.is_just:
            res["MIN_PASSWORD_SCORE"] = to_dict(self.min_password_score.value)
        if self.setting_token_time.is_just:
            res["SETTING_TOKEN_TIME"] = to_dict(self.setting_token_time.value)
        if self.max_number_of_files.is_just:
            res["MAX_NUMBER_OF_FILES"] = to_dict(
                self.max_number_of_files.value
            )
        if self.max_large_upload_size.is_just:
            res["MAX_LARGE_UPLOAD_SIZE"] = to_dict(
                self.max_large_upload_size.value
            )
        if self.max_normal_upload_size.is_just:
            res["MAX_NORMAL_UPLOAD_SIZE"] = to_dict(
                self.max_normal_upload_size.value
            )
        if self.max_dynamo_submission_size.is_just:
            res["MAX_DYNAMO_SUBMISSION_SIZE"] = to_dict(
                self.max_dynamo_submission_size.value
            )
        if self.max_file_size.is_just:
            res["MAX_FILE_SIZE"] = to_dict(self.max_file_size.value)
        if self.max_dynamo_file_size.is_just:
            res["MAX_DYNAMO_FILE_SIZE"] = to_dict(
                self.max_dynamo_file_size.value
            )
        if self.max_document_update_size.is_just:
            res["MAX_DOCUMENT_UPDATE_SIZE"] = to_dict(
                self.max_document_update_size.value
            )
        if self.jwt_access_token_expires.is_just:
            res["JWT_ACCESS_TOKEN_EXPIRES"] = to_dict(
                self.jwt_access_token_expires.value
            )
        if self.sso_username_decollision_enabled.is_just:
            res["SSO_USERNAME_DECOLLISION_ENABLED"] = to_dict(
                self.sso_username_decollision_enabled.value
            )
        if self.max_user_setting_amount.is_just:
            res["MAX_USER_SETTING_AMOUNT"] = to_dict(
                self.max_user_setting_amount.value
            )
        if self.send_registration_email.is_just:
            res["SEND_REGISTRATION_EMAIL"] = to_dict(
                self.send_registration_email.value
            )
        if self.automatic_lti_1p3_assignment_import.is_just:
            res["AUTOMATIC_LTI_1P3_ASSIGNMENT_IMPORT"] = to_dict(
                self.automatic_lti_1p3_assignment_import.value
            )
        if self.lti_unset_deadline_lock_date_enabled.is_just:
            res["LTI_UNSET_DEADLINE_LOCK_DATE_ENABLED"] = to_dict(
                self.lti_unset_deadline_lock_date_enabled.value
            )
        if self.lti_1p3_system_role_from_context_role.is_just:
            res["LTI_1P3_SYSTEM_ROLE_FROM_CONTEXT_ROLE"] = to_dict(
                self.lti_1p3_system_role_from_context_role.value
            )
        if self.lti_1p3_parse_most_privileged_role.is_just:
            res["LTI_1P3_PARSE_MOST_PRIVILEGED_ROLE"] = to_dict(
                self.lti_1p3_parse_most_privileged_role.value
            )
        if self.lti_launch_data_logging.is_just:
            res["LTI_LAUNCH_DATA_LOGGING"] = to_dict(
                self.lti_launch_data_logging.value
            )
        if self.pearson_templates.is_just:
            res["PEARSON_TEMPLATES"] = to_dict(self.pearson_templates.value)
        if self.default_course_teacher_role.is_just:
            res["DEFAULT_COURSE_TEACHER_ROLE"] = to_dict(
                self.default_course_teacher_role.value
            )
        if self.default_course_ta_role.is_just:
            res["DEFAULT_COURSE_TA_ROLE"] = to_dict(
                self.default_course_ta_role.value
            )
        if self.lti_1p3_nonce_and_state_validation_enabled.is_just:
            res["LTI_1P3_NONCE_AND_STATE_VALIDATION_ENABLED"] = to_dict(
                self.lti_1p3_nonce_and_state_validation_enabled.value
            )
        if self.lti_1p3_prevent_nonce_reuse_enabled.is_just:
            res["LTI_1P3_PREVENT_NONCE_REUSE_ENABLED"] = to_dict(
                self.lti_1p3_prevent_nonce_reuse_enabled.value
            )
        if self.name_and_email_from_nrps_only.is_just:
            res["NAME_AND_EMAIL_FROM_NRPS_ONLY"] = to_dict(
                self.name_and_email_from_nrps_only.value
            )
        if self.always_update_pii_with_lti.is_just:
            res["ALWAYS_UPDATE_PII_WITH_LTI"] = to_dict(
                self.always_update_pii_with_lti.value
            )
        if self.hubspot_syncing_enabled.is_just:
            res["HUBSPOT_SYNCING_ENABLED"] = to_dict(
                self.hubspot_syncing_enabled.value
            )
        if self.is_pearson.is_just:
            res["IS_PEARSON"] = to_dict(self.is_pearson.value)
        if self.lti_role_switching.is_just:
            res["LTI_ROLE_SWITCHING"] = to_dict(self.lti_role_switching.value)
        if self.per_course_payment_allowed.is_just:
            res["PER_COURSE_PAYMENT_ALLOWED"] = to_dict(
                self.per_course_payment_allowed.value
            )
        if self.payments_provider.is_just:
            res["PAYMENTS_PROVIDER"] = to_dict(self.payments_provider.value)
        if self.rubric_convert_use_atv2_enabled.is_just:
            res["RUBRIC_CONVERT_USE_ATV2_ENABLED"] = to_dict(
                self.rubric_convert_use_atv2_enabled.value
            )
        return res

    @classmethod
    def from_dict(
        cls: t.Type[AllSiteSettings], d: t.Dict[str, t.Any]
    ) -> AllSiteSettings:
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            auto_test_max_time_command=parsed.AUTO_TEST_MAX_TIME_COMMAND,
            auto_test_io_test_message=parsed.AUTO_TEST_IO_TEST_MESSAGE,
            auto_test_io_test_sub_message=parsed.AUTO_TEST_IO_TEST_SUB_MESSAGE,
            auto_test_run_program_message=parsed.AUTO_TEST_RUN_PROGRAM_MESSAGE,
            auto_test_capture_points_message=parsed.AUTO_TEST_CAPTURE_POINTS_MESSAGE,
            auto_test_checkpoint_message=parsed.AUTO_TEST_CHECKPOINT_MESSAGE,
            auto_test_unit_test_message=parsed.AUTO_TEST_UNIT_TEST_MESSAGE,
            auto_test_code_quality_message=parsed.AUTO_TEST_CODE_QUALITY_MESSAGE,
            new_auto_test_current_initial_build_ids=parsed.NEW_AUTO_TEST_CURRENT_INITIAL_BUILD_IDS,
            new_auto_test_build_max_command_time=parsed.NEW_AUTO_TEST_BUILD_MAX_COMMAND_TIME,
            new_auto_test_test_max_command_time=parsed.NEW_AUTO_TEST_TEST_MAX_COMMAND_TIME,
            code_editor_output_viewer_title=parsed.CODE_EDITOR_OUTPUT_VIEWER_TITLE,
            exam_login_max_length=parsed.EXAM_LOGIN_MAX_LENGTH,
            login_token_before_time=parsed.LOGIN_TOKEN_BEFORE_TIME,
            reset_token_time=parsed.RESET_TOKEN_TIME,
            site_email=parsed.SITE_EMAIL,
            access_token_toast_warning_time=parsed.ACCESS_TOKEN_TOAST_WARNING_TIME,
            access_token_modal_warning_time=parsed.ACCESS_TOKEN_MODAL_WARNING_TIME,
            max_lines=parsed.MAX_LINES,
            notification_poll_time=parsed.NOTIFICATION_POLL_TIME,
            release_message_max_time=parsed.RELEASE_MESSAGE_MAX_TIME,
            max_plagiarism_matches=parsed.MAX_PLAGIARISM_MATCHES,
            auto_test_max_global_setup_time=parsed.AUTO_TEST_MAX_GLOBAL_SETUP_TIME,
            auto_test_max_per_student_setup_time=parsed.AUTO_TEST_MAX_PER_STUDENT_SETUP_TIME,
            assignment_default_grading_scale=parsed.ASSIGNMENT_DEFAULT_GRADING_SCALE,
            assignment_default_grading_scale_points=parsed.ASSIGNMENT_DEFAULT_GRADING_SCALE_POINTS,
            blackboard_zip_upload_enabled=parsed.BLACKBOARD_ZIP_UPLOAD_ENABLED,
            rubric_enabled_for_teacher_on_submissions_page=parsed.RUBRIC_ENABLED_FOR_TEACHER_ON_SUBMISSIONS_PAGE,
            automatic_lti_role_enabled=parsed.AUTOMATIC_LTI_ROLE_ENABLED,
            register_enabled=parsed.REGISTER_ENABLED,
            groups_enabled=parsed.GROUPS_ENABLED,
            auto_test_enabled=parsed.AUTO_TEST_ENABLED,
            course_register_enabled=parsed.COURSE_REGISTER_ENABLED,
            render_html_enabled=parsed.RENDER_HTML_ENABLED,
            email_students_enabled=parsed.EMAIL_STUDENTS_ENABLED,
            peer_feedback_enabled=parsed.PEER_FEEDBACK_ENABLED,
            at_image_caching_enabled=parsed.AT_IMAGE_CACHING_ENABLED,
            student_payment_enabled=parsed.STUDENT_PAYMENT_ENABLED,
            student_payment_main_option=parsed.STUDENT_PAYMENT_MAIN_OPTION,
            editor_enabled=parsed.EDITOR_ENABLED,
            server_time_correction_enabled=parsed.SERVER_TIME_CORRECTION_ENABLED,
            grading_notifications_enabled=parsed.GRADING_NOTIFICATIONS_ENABLED,
            feedback_threads_initially_collapsed=parsed.FEEDBACK_THREADS_INITIALLY_COLLAPSED,
            server_time_diff_tolerance=parsed.SERVER_TIME_DIFF_TOLERANCE,
            server_time_sync_interval=parsed.SERVER_TIME_SYNC_INTERVAL,
            assignment_percentage_decimals=parsed.ASSIGNMENT_PERCENTAGE_DECIMALS,
            assignment_point_decimals=parsed.ASSIGNMENT_POINT_DECIMALS,
            output_viewer_animation_limit_lines_count=parsed.OUTPUT_VIEWER_ANIMATION_LIMIT_LINES_COUNT,
            output_viewer_auto_expand_failed_steps=parsed.OUTPUT_VIEWER_AUTO_EXPAND_FAILED_STEPS,
            lti_lock_date_copying_enabled=parsed.LTI_LOCK_DATE_COPYING_ENABLED,
            assignment_max_points_enabled=parsed.ASSIGNMENT_MAX_POINTS_ENABLED,
            course_gradebook_render_warning_size=parsed.COURSE_GRADEBOOK_RENDER_WARNING_SIZE,
            course_bulk_register_enabled=parsed.COURSE_BULK_REGISTER_ENABLED,
            csv_large_file_limit=parsed.CSV_LARGE_FILE_LIMIT,
            csv_too_many_errors_limit=parsed.CSV_TOO_MANY_ERRORS_LIMIT,
            new_auto_test_old_submission_age=parsed.NEW_AUTO_TEST_OLD_SUBMISSION_AGE,
            canvas_course_id_copying_enabled=parsed.CANVAS_COURSE_ID_COPYING_ENABLED,
            new_auto_test_diff_viewer_enabled=parsed.NEW_AUTO_TEST_DIFF_VIEWER_ENABLED,
            github_template_repo_enabled=parsed.GITHUB_TEMPLATE_REPO_ENABLED,
            community_library=parsed.COMMUNITY_LIBRARY,
            community_library_publishing=parsed.COMMUNITY_LIBRARY_PUBLISHING,
            quality_comments_in_code_editor=parsed.QUALITY_COMMENTS_IN_CODE_EDITOR,
            sso_infer_global_staff_role=parsed.SSO_INFER_GLOBAL_STAFF_ROLE,
            new_auto_test_uncollapsing_step_output_delay=parsed.NEW_AUTO_TEST_UNCOLLAPSING_STEP_OUTPUT_DELAY,
            assignment_description_on_teachers_submissions_page=parsed.ASSIGNMENT_DESCRIPTION_ON_TEACHERS_SUBMISSIONS_PAGE,
            inline_rubric_viewer_enabled=parsed.INLINE_RUBRIC_VIEWER_ENABLED,
            hide_code_editor_output_viewer_with_only_quiz_steps=parsed.HIDE_CODE_EDITOR_OUTPUT_VIEWER_WITH_ONLY_QUIZ_STEPS,
            hide_code_editor_filetree_controls_with_only_quiz_steps=parsed.HIDE_CODE_EDITOR_FILETREE_CONTROLS_WITH_ONLY_QUIZ_STEPS,
            simple_submission_navigate_to_latest_editor_session=parsed.SIMPLE_SUBMISSION_NAVIGATE_TO_LATEST_EDITOR_SESSION,
            display_grades_enabled=parsed.DISPLAY_GRADES_ENABLED,
            hide_empty_rubric_row_description=parsed.HIDE_EMPTY_RUBRIC_ROW_DESCRIPTION,
            default_submission_page_tab=parsed.DEFAULT_SUBMISSION_PAGE_TAB,
            hide_no_deadline_enabled=parsed.HIDE_NO_DEADLINE_ENABLED,
            retry_group_submission_grade_passback_enabled=parsed.RETRY_GROUP_SUBMISSION_GRADE_PASSBACK_ENABLED,
            code_editor_start_on_assignment_description=parsed.CODE_EDITOR_START_ON_ASSIGNMENT_DESCRIPTION,
            ai_assistant_enabled=parsed.AI_ASSISTANT_ENABLED,
            assistant_tools_enabled=parsed.ASSISTANT_TOOLS_ENABLED,
            prompt_engineering_step_enabled=parsed.PROMPT_ENGINEERING_STEP_ENABLED,
            first_day_of_week_from_locale=parsed.FIRST_DAY_OF_WEEK_FROM_LOCALE,
            inline_feedback_on_quizzes_enabled=parsed.INLINE_FEEDBACK_ON_QUIZZES_ENABLED,
            quiz_single_question_mode_hide_run_button_enabled=parsed.QUIZ_SINGLE_QUESTION_MODE_HIDE_RUN_BUTTON_ENABLED,
            warning_for_missing_newline_enabled=parsed.WARNING_FOR_MISSING_NEWLINE_ENABLED,
            jupyter_notebook_editor_enabled=parsed.JUPYTER_NOTEBOOK_EDITOR_ENABLED,
            jupyter_notebook_running_enabled=parsed.JUPYTER_NOTEBOOK_RUNNING_ENABLED,
            coding_question_editor_reset_answer_enabled=parsed.CODING_QUESTION_EDITOR_RESET_ANSWER_ENABLED,
            coding_question_solution_enabled=parsed.CODING_QUESTION_SOLUTION_ENABLED,
            download_editor_files_enabled=parsed.DOWNLOAD_EDITOR_FILES_ENABLED,
            quiz_view_modes_enabled=parsed.QUIZ_VIEW_MODES_ENABLED,
            regex_atv2_explanation_enabled=parsed.REGEX_ATV2_EXPLANATION_ENABLED,
            auto_test_heartbeat_interval=parsed.AUTO_TEST_HEARTBEAT_INTERVAL,
            auto_test_heartbeat_max_missed=parsed.AUTO_TEST_HEARTBEAT_MAX_MISSED,
            auto_test_max_jobs_per_runner=parsed.AUTO_TEST_MAX_JOBS_PER_RUNNER,
            auto_test_max_concurrent_batch_runs=parsed.AUTO_TEST_MAX_CONCURRENT_BATCH_RUNS,
            auto_test_max_result_not_started=parsed.AUTO_TEST_MAX_RESULT_NOT_STARTED,
            auto_test_max_unit_test_metadata_length=parsed.AUTO_TEST_MAX_UNIT_TEST_METADATA_LENGTH,
            new_auto_test_max_dynamodb_size=parsed.NEW_AUTO_TEST_MAX_DYNAMODB_SIZE,
            new_auto_test_max_storage_size=parsed.NEW_AUTO_TEST_MAX_STORAGE_SIZE,
            new_auto_test_max_file_size=parsed.NEW_AUTO_TEST_MAX_FILE_SIZE,
            new_auto_test_build_output_limit=parsed.NEW_AUTO_TEST_BUILD_OUTPUT_LIMIT,
            new_auto_test_test_output_limit=parsed.NEW_AUTO_TEST_TEST_OUTPUT_LIMIT,
            new_auto_test_max_output_files_size=parsed.NEW_AUTO_TEST_MAX_OUTPUT_FILES_SIZE,
            new_auto_test_allowed_initial_build_ids=parsed.NEW_AUTO_TEST_ALLOWED_INITIAL_BUILD_IDS,
            new_auto_test_initial_build_id=parsed.NEW_AUTO_TEST_INITIAL_BUILD_ID,
            min_password_score=parsed.MIN_PASSWORD_SCORE,
            setting_token_time=parsed.SETTING_TOKEN_TIME,
            max_number_of_files=parsed.MAX_NUMBER_OF_FILES,
            max_large_upload_size=parsed.MAX_LARGE_UPLOAD_SIZE,
            max_normal_upload_size=parsed.MAX_NORMAL_UPLOAD_SIZE,
            max_dynamo_submission_size=parsed.MAX_DYNAMO_SUBMISSION_SIZE,
            max_file_size=parsed.MAX_FILE_SIZE,
            max_dynamo_file_size=parsed.MAX_DYNAMO_FILE_SIZE,
            max_document_update_size=parsed.MAX_DOCUMENT_UPDATE_SIZE,
            jwt_access_token_expires=parsed.JWT_ACCESS_TOKEN_EXPIRES,
            sso_username_decollision_enabled=parsed.SSO_USERNAME_DECOLLISION_ENABLED,
            max_user_setting_amount=parsed.MAX_USER_SETTING_AMOUNT,
            send_registration_email=parsed.SEND_REGISTRATION_EMAIL,
            automatic_lti_1p3_assignment_import=parsed.AUTOMATIC_LTI_1P3_ASSIGNMENT_IMPORT,
            lti_unset_deadline_lock_date_enabled=parsed.LTI_UNSET_DEADLINE_LOCK_DATE_ENABLED,
            lti_1p3_system_role_from_context_role=parsed.LTI_1P3_SYSTEM_ROLE_FROM_CONTEXT_ROLE,
            lti_1p3_parse_most_privileged_role=parsed.LTI_1P3_PARSE_MOST_PRIVILEGED_ROLE,
            lti_launch_data_logging=parsed.LTI_LAUNCH_DATA_LOGGING,
            pearson_templates=parsed.PEARSON_TEMPLATES,
            default_course_teacher_role=parsed.DEFAULT_COURSE_TEACHER_ROLE,
            default_course_ta_role=parsed.DEFAULT_COURSE_TA_ROLE,
            lti_1p3_nonce_and_state_validation_enabled=parsed.LTI_1P3_NONCE_AND_STATE_VALIDATION_ENABLED,
            lti_1p3_prevent_nonce_reuse_enabled=parsed.LTI_1P3_PREVENT_NONCE_REUSE_ENABLED,
            name_and_email_from_nrps_only=parsed.NAME_AND_EMAIL_FROM_NRPS_ONLY,
            always_update_pii_with_lti=parsed.ALWAYS_UPDATE_PII_WITH_LTI,
            hubspot_syncing_enabled=parsed.HUBSPOT_SYNCING_ENABLED,
            is_pearson=parsed.IS_PEARSON,
            lti_role_switching=parsed.LTI_ROLE_SWITCHING,
            per_course_payment_allowed=parsed.PER_COURSE_PAYMENT_ALLOWED,
            payments_provider=parsed.PAYMENTS_PROVIDER,
            rubric_convert_use_atv2_enabled=parsed.RUBRIC_CONVERT_USE_ATV2_ENABLED,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    from .fraction import Fraction
