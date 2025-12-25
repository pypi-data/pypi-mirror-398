"""The module that defines the ``SiteSettingInput`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from ..parsers import ParserFor, make_union
from ..utils import to_dict
from .access_token_modal_warning_time_setting import (
    AccessTokenModalWarningTimeSetting,
)
from .access_token_toast_warning_time_setting import (
    AccessTokenToastWarningTimeSetting,
)
from .ai_assistant_enabled_setting import AiAssistantEnabledSetting
from .always_update_pii_with_lti_setting import AlwaysUpdatePiiWithLtiSetting
from .assignment_default_grading_scale_points_setting import (
    AssignmentDefaultGradingScalePointsSetting,
)
from .assignment_default_grading_scale_setting import (
    AssignmentDefaultGradingScaleSetting,
)
from .assignment_description_on_teachers_submissions_page_setting import (
    AssignmentDescriptionOnTeachersSubmissionsPageSetting,
)
from .assignment_max_points_enabled_setting import (
    AssignmentMaxPointsEnabledSetting,
)
from .assignment_percentage_decimals_setting import (
    AssignmentPercentageDecimalsSetting,
)
from .assignment_point_decimals_setting import AssignmentPointDecimalsSetting
from .assistant_tools_enabled_setting import AssistantToolsEnabledSetting
from .at_image_caching_enabled_setting import AtImageCachingEnabledSetting
from .auto_test_capture_points_message_setting import (
    AutoTestCapturePointsMessageSetting,
)
from .auto_test_checkpoint_message_setting import (
    AutoTestCheckpointMessageSetting,
)
from .auto_test_code_quality_message_setting import (
    AutoTestCodeQualityMessageSetting,
)
from .auto_test_enabled_setting import AutoTestEnabledSetting
from .auto_test_heartbeat_interval_setting import (
    AutoTestHeartbeatIntervalSetting,
)
from .auto_test_heartbeat_max_missed_setting import (
    AutoTestHeartbeatMaxMissedSetting,
)
from .auto_test_io_test_message_setting import AutoTestIoTestMessageSetting
from .auto_test_io_test_sub_message_setting import (
    AutoTestIoTestSubMessageSetting,
)
from .auto_test_max_concurrent_batch_runs_setting import (
    AutoTestMaxConcurrentBatchRunsSetting,
)
from .auto_test_max_global_setup_time_setting import (
    AutoTestMaxGlobalSetupTimeSetting,
)
from .auto_test_max_jobs_per_runner_setting import (
    AutoTestMaxJobsPerRunnerSetting,
)
from .auto_test_max_per_student_setup_time_setting import (
    AutoTestMaxPerStudentSetupTimeSetting,
)
from .auto_test_max_result_not_started_setting import (
    AutoTestMaxResultNotStartedSetting,
)
from .auto_test_max_time_command_setting import AutoTestMaxTimeCommandSetting
from .auto_test_max_unit_test_metadata_length_setting import (
    AutoTestMaxUnitTestMetadataLengthSetting,
)
from .auto_test_run_program_message_setting import (
    AutoTestRunProgramMessageSetting,
)
from .auto_test_unit_test_message_setting import AutoTestUnitTestMessageSetting
from .automatic_lti1p3_assignment_import_setting import (
    AutomaticLti1p3AssignmentImportSetting,
)
from .automatic_lti_role_enabled_setting import AutomaticLtiRoleEnabledSetting
from .blackboard_zip_upload_enabled_setting import (
    BlackboardZipUploadEnabledSetting,
)
from .canvas_course_id_copying_enabled_setting import (
    CanvasCourseIdCopyingEnabledSetting,
)
from .code_editor_output_viewer_title_setting import (
    CodeEditorOutputViewerTitleSetting,
)
from .code_editor_start_on_assignment_description_setting import (
    CodeEditorStartOnAssignmentDescriptionSetting,
)
from .coding_question_editor_reset_answer_enabled_setting import (
    CodingQuestionEditorResetAnswerEnabledSetting,
)
from .coding_question_solution_enabled_setting import (
    CodingQuestionSolutionEnabledSetting,
)
from .community_library_publishing_setting import (
    CommunityLibraryPublishingSetting,
)
from .community_library_setting import CommunityLibrarySetting
from .course_bulk_register_enabled_setting import (
    CourseBulkRegisterEnabledSetting,
)
from .course_gradebook_render_warning_size_setting import (
    CourseGradebookRenderWarningSizeSetting,
)
from .course_register_enabled_setting import CourseRegisterEnabledSetting
from .csv_large_file_limit_setting import CsvLargeFileLimitSetting
from .csv_too_many_errors_limit_setting import CsvTooManyErrorsLimitSetting
from .default_course_ta_role_setting import DefaultCourseTaRoleSetting
from .default_course_teacher_role_setting import (
    DefaultCourseTeacherRoleSetting,
)
from .default_submission_page_tab_setting import (
    DefaultSubmissionPageTabSetting,
)
from .display_grades_enabled_setting import DisplayGradesEnabledSetting
from .download_editor_files_enabled_setting import (
    DownloadEditorFilesEnabledSetting,
)
from .editor_enabled_setting import EditorEnabledSetting
from .email_students_enabled_setting import EmailStudentsEnabledSetting
from .exam_login_max_length_setting import ExamLoginMaxLengthSetting
from .feedback_threads_initially_collapsed_setting import (
    FeedbackThreadsInitiallyCollapsedSetting,
)
from .first_day_of_week_from_locale_setting import (
    FirstDayOfWeekFromLocaleSetting,
)
from .github_template_repo_enabled_setting import (
    GithubTemplateRepoEnabledSetting,
)
from .grading_notifications_enabled_setting import (
    GradingNotificationsEnabledSetting,
)
from .groups_enabled_setting import GroupsEnabledSetting
from .hide_code_editor_filetree_controls_with_only_quiz_steps_setting import (
    HideCodeEditorFiletreeControlsWithOnlyQuizStepsSetting,
)
from .hide_code_editor_output_viewer_with_only_quiz_steps_setting import (
    HideCodeEditorOutputViewerWithOnlyQuizStepsSetting,
)
from .hide_empty_rubric_row_description_setting import (
    HideEmptyRubricRowDescriptionSetting,
)
from .hide_no_deadline_enabled_setting import HideNoDeadlineEnabledSetting
from .hubspot_syncing_enabled_setting import HubspotSyncingEnabledSetting
from .inline_feedback_on_quizzes_enabled_setting import (
    InlineFeedbackOnQuizzesEnabledSetting,
)
from .inline_rubric_viewer_enabled_setting import (
    InlineRubricViewerEnabledSetting,
)
from .is_pearson_setting import IsPearsonSetting
from .jupyter_notebook_editor_enabled_setting import (
    JupyterNotebookEditorEnabledSetting,
)
from .jupyter_notebook_running_enabled_setting import (
    JupyterNotebookRunningEnabledSetting,
)
from .jwt_access_token_expires_setting import JwtAccessTokenExpiresSetting
from .login_token_before_time_setting import LoginTokenBeforeTimeSetting
from .lti1p3_nonce_and_state_validation_enabled_setting import (
    Lti1p3NonceAndStateValidationEnabledSetting,
)
from .lti1p3_parse_most_privileged_role_setting import (
    Lti1p3ParseMostPrivilegedRoleSetting,
)
from .lti1p3_prevent_nonce_reuse_enabled_setting import (
    Lti1p3PreventNonceReuseEnabledSetting,
)
from .lti1p3_system_role_from_context_role_setting import (
    Lti1p3SystemRoleFromContextRoleSetting,
)
from .lti_launch_data_logging_setting import LtiLaunchDataLoggingSetting
from .lti_lock_date_copying_enabled_setting import (
    LtiLockDateCopyingEnabledSetting,
)
from .lti_role_switching_setting import LtiRoleSwitchingSetting
from .lti_unset_deadline_lock_date_enabled_setting import (
    LtiUnsetDeadlineLockDateEnabledSetting,
)
from .max_document_update_size_setting import MaxDocumentUpdateSizeSetting
from .max_dynamo_file_size_setting import MaxDynamoFileSizeSetting
from .max_dynamo_submission_size_setting import MaxDynamoSubmissionSizeSetting
from .max_file_size_setting import MaxFileSizeSetting
from .max_large_upload_size_setting import MaxLargeUploadSizeSetting
from .max_lines_setting import MaxLinesSetting
from .max_normal_upload_size_setting import MaxNormalUploadSizeSetting
from .max_number_of_files_setting import MaxNumberOfFilesSetting
from .max_plagiarism_matches_setting import MaxPlagiarismMatchesSetting
from .max_user_setting_amount_setting import MaxUserSettingAmountSetting
from .min_password_score_setting import MinPasswordScoreSetting
from .name_and_email_from_nrps_only_setting import (
    NameAndEmailFromNrpsOnlySetting,
)
from .new_auto_test_allowed_initial_build_ids_setting import (
    NewAutoTestAllowedInitialBuildIdsSetting,
)
from .new_auto_test_build_max_command_time_setting import (
    NewAutoTestBuildMaxCommandTimeSetting,
)
from .new_auto_test_build_output_limit_setting import (
    NewAutoTestBuildOutputLimitSetting,
)
from .new_auto_test_current_initial_build_ids_setting import (
    NewAutoTestCurrentInitialBuildIdsSetting,
)
from .new_auto_test_diff_viewer_enabled_setting import (
    NewAutoTestDiffViewerEnabledSetting,
)
from .new_auto_test_initial_build_id_setting import (
    NewAutoTestInitialBuildIdSetting,
)
from .new_auto_test_max_dynamodb_size_setting import (
    NewAutoTestMaxDynamodbSizeSetting,
)
from .new_auto_test_max_file_size_setting import NewAutoTestMaxFileSizeSetting
from .new_auto_test_max_output_files_size_setting import (
    NewAutoTestMaxOutputFilesSizeSetting,
)
from .new_auto_test_max_storage_size_setting import (
    NewAutoTestMaxStorageSizeSetting,
)
from .new_auto_test_old_submission_age_setting import (
    NewAutoTestOldSubmissionAgeSetting,
)
from .new_auto_test_test_max_command_time_setting import (
    NewAutoTestTestMaxCommandTimeSetting,
)
from .new_auto_test_test_output_limit_setting import (
    NewAutoTestTestOutputLimitSetting,
)
from .new_auto_test_uncollapsing_step_output_delay_setting import (
    NewAutoTestUncollapsingStepOutputDelaySetting,
)
from .notification_poll_time_setting import NotificationPollTimeSetting
from .output_viewer_animation_limit_lines_count_setting import (
    OutputViewerAnimationLimitLinesCountSetting,
)
from .output_viewer_auto_expand_failed_steps_setting import (
    OutputViewerAutoExpandFailedStepsSetting,
)
from .payments_provider_setting import PaymentsProviderSetting
from .pearson_templates_setting import PearsonTemplatesSetting
from .peer_feedback_enabled_setting import PeerFeedbackEnabledSetting
from .per_course_payment_allowed_setting import PerCoursePaymentAllowedSetting
from .prompt_engineering_step_enabled_setting import (
    PromptEngineeringStepEnabledSetting,
)
from .quality_comments_in_code_editor_setting import (
    QualityCommentsInCodeEditorSetting,
)
from .quiz_single_question_mode_hide_run_button_enabled_setting import (
    QuizSingleQuestionModeHideRunButtonEnabledSetting,
)
from .quiz_view_modes_enabled_setting import QuizViewModesEnabledSetting
from .regex_atv2_explanation_enabled_setting import (
    RegexAtv2ExplanationEnabledSetting,
)
from .register_enabled_setting import RegisterEnabledSetting
from .release_message_max_time_setting import ReleaseMessageMaxTimeSetting
from .render_html_enabled_setting import RenderHtmlEnabledSetting
from .reset_token_time_setting import ResetTokenTimeSetting
from .retry_group_submission_grade_passback_enabled_setting import (
    RetryGroupSubmissionGradePassbackEnabledSetting,
)
from .rubric_convert_use_atv2_enabled_setting import (
    RubricConvertUseAtv2EnabledSetting,
)
from .rubric_enabled_for_teacher_on_submissions_page_setting import (
    RubricEnabledForTeacherOnSubmissionsPageSetting,
)
from .send_registration_email_setting import SendRegistrationEmailSetting
from .server_time_correction_enabled_setting import (
    ServerTimeCorrectionEnabledSetting,
)
from .server_time_diff_tolerance_setting import ServerTimeDiffToleranceSetting
from .server_time_sync_interval_setting import ServerTimeSyncIntervalSetting
from .setting_token_time_setting import SettingTokenTimeSetting
from .simple_submission_navigate_to_latest_editor_session_setting import (
    SimpleSubmissionNavigateToLatestEditorSessionSetting,
)
from .site_email_setting import SiteEmailSetting
from .sso_infer_global_staff_role_setting import SsoInferGlobalStaffRoleSetting
from .sso_username_decollision_enabled_setting import (
    SsoUsernameDecollisionEnabledSetting,
)
from .student_payment_enabled_setting import StudentPaymentEnabledSetting
from .student_payment_main_option_setting import (
    StudentPaymentMainOptionSetting,
)
from .warning_for_missing_newline_enabled_setting import (
    WarningForMissingNewlineEnabledSetting,
)

SiteSettingInput = t.Union[
    AutoTestMaxTimeCommandSetting,
    AutoTestHeartbeatIntervalSetting,
    AutoTestHeartbeatMaxMissedSetting,
    AutoTestMaxJobsPerRunnerSetting,
    AutoTestMaxConcurrentBatchRunsSetting,
    AutoTestIoTestMessageSetting,
    AutoTestIoTestSubMessageSetting,
    AutoTestRunProgramMessageSetting,
    AutoTestCapturePointsMessageSetting,
    AutoTestCheckpointMessageSetting,
    AutoTestUnitTestMessageSetting,
    AutoTestCodeQualityMessageSetting,
    AutoTestMaxResultNotStartedSetting,
    AutoTestMaxUnitTestMetadataLengthSetting,
    NewAutoTestMaxDynamodbSizeSetting,
    NewAutoTestMaxStorageSizeSetting,
    NewAutoTestMaxFileSizeSetting,
    NewAutoTestBuildOutputLimitSetting,
    NewAutoTestTestOutputLimitSetting,
    NewAutoTestMaxOutputFilesSizeSetting,
    NewAutoTestCurrentInitialBuildIdsSetting,
    NewAutoTestAllowedInitialBuildIdsSetting,
    NewAutoTestInitialBuildIdSetting,
    NewAutoTestBuildMaxCommandTimeSetting,
    NewAutoTestTestMaxCommandTimeSetting,
    CodeEditorOutputViewerTitleSetting,
    ExamLoginMaxLengthSetting,
    LoginTokenBeforeTimeSetting,
    MinPasswordScoreSetting,
    ResetTokenTimeSetting,
    SettingTokenTimeSetting,
    SiteEmailSetting,
    MaxNumberOfFilesSetting,
    MaxLargeUploadSizeSetting,
    MaxNormalUploadSizeSetting,
    MaxDynamoSubmissionSizeSetting,
    MaxFileSizeSetting,
    MaxDynamoFileSizeSetting,
    MaxDocumentUpdateSizeSetting,
    JwtAccessTokenExpiresSetting,
    AccessTokenToastWarningTimeSetting,
    AccessTokenModalWarningTimeSetting,
    MaxLinesSetting,
    NotificationPollTimeSetting,
    ReleaseMessageMaxTimeSetting,
    MaxPlagiarismMatchesSetting,
    AutoTestMaxGlobalSetupTimeSetting,
    AutoTestMaxPerStudentSetupTimeSetting,
    AssignmentDefaultGradingScaleSetting,
    AssignmentDefaultGradingScalePointsSetting,
    BlackboardZipUploadEnabledSetting,
    RubricEnabledForTeacherOnSubmissionsPageSetting,
    AutomaticLtiRoleEnabledSetting,
    RegisterEnabledSetting,
    GroupsEnabledSetting,
    AutoTestEnabledSetting,
    CourseRegisterEnabledSetting,
    RenderHtmlEnabledSetting,
    EmailStudentsEnabledSetting,
    PeerFeedbackEnabledSetting,
    AtImageCachingEnabledSetting,
    StudentPaymentEnabledSetting,
    StudentPaymentMainOptionSetting,
    EditorEnabledSetting,
    ServerTimeCorrectionEnabledSetting,
    GradingNotificationsEnabledSetting,
    SsoUsernameDecollisionEnabledSetting,
    FeedbackThreadsInitiallyCollapsedSetting,
    MaxUserSettingAmountSetting,
    SendRegistrationEmailSetting,
    ServerTimeDiffToleranceSetting,
    ServerTimeSyncIntervalSetting,
    AutomaticLti1p3AssignmentImportSetting,
    AssignmentPercentageDecimalsSetting,
    AssignmentPointDecimalsSetting,
    OutputViewerAnimationLimitLinesCountSetting,
    OutputViewerAutoExpandFailedStepsSetting,
    LtiLockDateCopyingEnabledSetting,
    AssignmentMaxPointsEnabledSetting,
    CourseGradebookRenderWarningSizeSetting,
    CourseBulkRegisterEnabledSetting,
    CsvLargeFileLimitSetting,
    CsvTooManyErrorsLimitSetting,
    NewAutoTestOldSubmissionAgeSetting,
    CanvasCourseIdCopyingEnabledSetting,
    NewAutoTestDiffViewerEnabledSetting,
    LtiUnsetDeadlineLockDateEnabledSetting,
    GithubTemplateRepoEnabledSetting,
    CommunityLibrarySetting,
    CommunityLibraryPublishingSetting,
    Lti1p3SystemRoleFromContextRoleSetting,
    Lti1p3ParseMostPrivilegedRoleSetting,
    QualityCommentsInCodeEditorSetting,
    SsoInferGlobalStaffRoleSetting,
    NewAutoTestUncollapsingStepOutputDelaySetting,
    AssignmentDescriptionOnTeachersSubmissionsPageSetting,
    InlineRubricViewerEnabledSetting,
    LtiLaunchDataLoggingSetting,
    HideCodeEditorOutputViewerWithOnlyQuizStepsSetting,
    HideCodeEditorFiletreeControlsWithOnlyQuizStepsSetting,
    PearsonTemplatesSetting,
    SimpleSubmissionNavigateToLatestEditorSessionSetting,
    DisplayGradesEnabledSetting,
    HideEmptyRubricRowDescriptionSetting,
    DefaultCourseTeacherRoleSetting,
    DefaultCourseTaRoleSetting,
    Lti1p3NonceAndStateValidationEnabledSetting,
    Lti1p3PreventNonceReuseEnabledSetting,
    DefaultSubmissionPageTabSetting,
    NameAndEmailFromNrpsOnlySetting,
    AlwaysUpdatePiiWithLtiSetting,
    HubspotSyncingEnabledSetting,
    HideNoDeadlineEnabledSetting,
    RetryGroupSubmissionGradePassbackEnabledSetting,
    CodeEditorStartOnAssignmentDescriptionSetting,
    AiAssistantEnabledSetting,
    AssistantToolsEnabledSetting,
    PromptEngineeringStepEnabledSetting,
    FirstDayOfWeekFromLocaleSetting,
    InlineFeedbackOnQuizzesEnabledSetting,
    IsPearsonSetting,
    QuizSingleQuestionModeHideRunButtonEnabledSetting,
    WarningForMissingNewlineEnabledSetting,
    JupyterNotebookEditorEnabledSetting,
    JupyterNotebookRunningEnabledSetting,
    LtiRoleSwitchingSetting,
    CodingQuestionEditorResetAnswerEnabledSetting,
    CodingQuestionSolutionEnabledSetting,
    PerCoursePaymentAllowedSetting,
    DownloadEditorFilesEnabledSetting,
    PaymentsProviderSetting,
    QuizViewModesEnabledSetting,
    RubricConvertUseAtv2EnabledSetting,
    RegexAtv2ExplanationEnabledSetting,
]
SiteSettingInputParser = rqa.Lazy(
    lambda: make_union(
        ParserFor.make(AutoTestMaxTimeCommandSetting),
        ParserFor.make(AutoTestHeartbeatIntervalSetting),
        ParserFor.make(AutoTestHeartbeatMaxMissedSetting),
        ParserFor.make(AutoTestMaxJobsPerRunnerSetting),
        ParserFor.make(AutoTestMaxConcurrentBatchRunsSetting),
        ParserFor.make(AutoTestIoTestMessageSetting),
        ParserFor.make(AutoTestIoTestSubMessageSetting),
        ParserFor.make(AutoTestRunProgramMessageSetting),
        ParserFor.make(AutoTestCapturePointsMessageSetting),
        ParserFor.make(AutoTestCheckpointMessageSetting),
        ParserFor.make(AutoTestUnitTestMessageSetting),
        ParserFor.make(AutoTestCodeQualityMessageSetting),
        ParserFor.make(AutoTestMaxResultNotStartedSetting),
        ParserFor.make(AutoTestMaxUnitTestMetadataLengthSetting),
        ParserFor.make(NewAutoTestMaxDynamodbSizeSetting),
        ParserFor.make(NewAutoTestMaxStorageSizeSetting),
        ParserFor.make(NewAutoTestMaxFileSizeSetting),
        ParserFor.make(NewAutoTestBuildOutputLimitSetting),
        ParserFor.make(NewAutoTestTestOutputLimitSetting),
        ParserFor.make(NewAutoTestMaxOutputFilesSizeSetting),
        ParserFor.make(NewAutoTestCurrentInitialBuildIdsSetting),
        ParserFor.make(NewAutoTestAllowedInitialBuildIdsSetting),
        ParserFor.make(NewAutoTestInitialBuildIdSetting),
        ParserFor.make(NewAutoTestBuildMaxCommandTimeSetting),
        ParserFor.make(NewAutoTestTestMaxCommandTimeSetting),
        ParserFor.make(CodeEditorOutputViewerTitleSetting),
        ParserFor.make(ExamLoginMaxLengthSetting),
        ParserFor.make(LoginTokenBeforeTimeSetting),
        ParserFor.make(MinPasswordScoreSetting),
        ParserFor.make(ResetTokenTimeSetting),
        ParserFor.make(SettingTokenTimeSetting),
        ParserFor.make(SiteEmailSetting),
        ParserFor.make(MaxNumberOfFilesSetting),
        ParserFor.make(MaxLargeUploadSizeSetting),
        ParserFor.make(MaxNormalUploadSizeSetting),
        ParserFor.make(MaxDynamoSubmissionSizeSetting),
        ParserFor.make(MaxFileSizeSetting),
        ParserFor.make(MaxDynamoFileSizeSetting),
        ParserFor.make(MaxDocumentUpdateSizeSetting),
        ParserFor.make(JwtAccessTokenExpiresSetting),
        ParserFor.make(AccessTokenToastWarningTimeSetting),
        ParserFor.make(AccessTokenModalWarningTimeSetting),
        ParserFor.make(MaxLinesSetting),
        ParserFor.make(NotificationPollTimeSetting),
        ParserFor.make(ReleaseMessageMaxTimeSetting),
        ParserFor.make(MaxPlagiarismMatchesSetting),
        ParserFor.make(AutoTestMaxGlobalSetupTimeSetting),
        ParserFor.make(AutoTestMaxPerStudentSetupTimeSetting),
        ParserFor.make(AssignmentDefaultGradingScaleSetting),
        ParserFor.make(AssignmentDefaultGradingScalePointsSetting),
        ParserFor.make(BlackboardZipUploadEnabledSetting),
        ParserFor.make(RubricEnabledForTeacherOnSubmissionsPageSetting),
        ParserFor.make(AutomaticLtiRoleEnabledSetting),
        ParserFor.make(RegisterEnabledSetting),
        ParserFor.make(GroupsEnabledSetting),
        ParserFor.make(AutoTestEnabledSetting),
        ParserFor.make(CourseRegisterEnabledSetting),
        ParserFor.make(RenderHtmlEnabledSetting),
        ParserFor.make(EmailStudentsEnabledSetting),
        ParserFor.make(PeerFeedbackEnabledSetting),
        ParserFor.make(AtImageCachingEnabledSetting),
        ParserFor.make(StudentPaymentEnabledSetting),
        ParserFor.make(StudentPaymentMainOptionSetting),
        ParserFor.make(EditorEnabledSetting),
        ParserFor.make(ServerTimeCorrectionEnabledSetting),
        ParserFor.make(GradingNotificationsEnabledSetting),
        ParserFor.make(SsoUsernameDecollisionEnabledSetting),
        ParserFor.make(FeedbackThreadsInitiallyCollapsedSetting),
        ParserFor.make(MaxUserSettingAmountSetting),
        ParserFor.make(SendRegistrationEmailSetting),
        ParserFor.make(ServerTimeDiffToleranceSetting),
        ParserFor.make(ServerTimeSyncIntervalSetting),
        ParserFor.make(AutomaticLti1p3AssignmentImportSetting),
        ParserFor.make(AssignmentPercentageDecimalsSetting),
        ParserFor.make(AssignmentPointDecimalsSetting),
        ParserFor.make(OutputViewerAnimationLimitLinesCountSetting),
        ParserFor.make(OutputViewerAutoExpandFailedStepsSetting),
        ParserFor.make(LtiLockDateCopyingEnabledSetting),
        ParserFor.make(AssignmentMaxPointsEnabledSetting),
        ParserFor.make(CourseGradebookRenderWarningSizeSetting),
        ParserFor.make(CourseBulkRegisterEnabledSetting),
        ParserFor.make(CsvLargeFileLimitSetting),
        ParserFor.make(CsvTooManyErrorsLimitSetting),
        ParserFor.make(NewAutoTestOldSubmissionAgeSetting),
        ParserFor.make(CanvasCourseIdCopyingEnabledSetting),
        ParserFor.make(NewAutoTestDiffViewerEnabledSetting),
        ParserFor.make(LtiUnsetDeadlineLockDateEnabledSetting),
        ParserFor.make(GithubTemplateRepoEnabledSetting),
        ParserFor.make(CommunityLibrarySetting),
        ParserFor.make(CommunityLibraryPublishingSetting),
        ParserFor.make(Lti1p3SystemRoleFromContextRoleSetting),
        ParserFor.make(Lti1p3ParseMostPrivilegedRoleSetting),
        ParserFor.make(QualityCommentsInCodeEditorSetting),
        ParserFor.make(SsoInferGlobalStaffRoleSetting),
        ParserFor.make(NewAutoTestUncollapsingStepOutputDelaySetting),
        ParserFor.make(AssignmentDescriptionOnTeachersSubmissionsPageSetting),
        ParserFor.make(InlineRubricViewerEnabledSetting),
        ParserFor.make(LtiLaunchDataLoggingSetting),
        ParserFor.make(HideCodeEditorOutputViewerWithOnlyQuizStepsSetting),
        ParserFor.make(HideCodeEditorFiletreeControlsWithOnlyQuizStepsSetting),
        ParserFor.make(PearsonTemplatesSetting),
        ParserFor.make(SimpleSubmissionNavigateToLatestEditorSessionSetting),
        ParserFor.make(DisplayGradesEnabledSetting),
        ParserFor.make(HideEmptyRubricRowDescriptionSetting),
        ParserFor.make(DefaultCourseTeacherRoleSetting),
        ParserFor.make(DefaultCourseTaRoleSetting),
        ParserFor.make(Lti1p3NonceAndStateValidationEnabledSetting),
        ParserFor.make(Lti1p3PreventNonceReuseEnabledSetting),
        ParserFor.make(DefaultSubmissionPageTabSetting),
        ParserFor.make(NameAndEmailFromNrpsOnlySetting),
        ParserFor.make(AlwaysUpdatePiiWithLtiSetting),
        ParserFor.make(HubspotSyncingEnabledSetting),
        ParserFor.make(HideNoDeadlineEnabledSetting),
        ParserFor.make(RetryGroupSubmissionGradePassbackEnabledSetting),
        ParserFor.make(CodeEditorStartOnAssignmentDescriptionSetting),
        ParserFor.make(AiAssistantEnabledSetting),
        ParserFor.make(AssistantToolsEnabledSetting),
        ParserFor.make(PromptEngineeringStepEnabledSetting),
        ParserFor.make(FirstDayOfWeekFromLocaleSetting),
        ParserFor.make(InlineFeedbackOnQuizzesEnabledSetting),
        ParserFor.make(IsPearsonSetting),
        ParserFor.make(QuizSingleQuestionModeHideRunButtonEnabledSetting),
        ParserFor.make(WarningForMissingNewlineEnabledSetting),
        ParserFor.make(JupyterNotebookEditorEnabledSetting),
        ParserFor.make(JupyterNotebookRunningEnabledSetting),
        ParserFor.make(LtiRoleSwitchingSetting),
        ParserFor.make(CodingQuestionEditorResetAnswerEnabledSetting),
        ParserFor.make(CodingQuestionSolutionEnabledSetting),
        ParserFor.make(PerCoursePaymentAllowedSetting),
        ParserFor.make(DownloadEditorFilesEnabledSetting),
        ParserFor.make(PaymentsProviderSetting),
        ParserFor.make(QuizViewModesEnabledSetting),
        ParserFor.make(RubricConvertUseAtv2EnabledSetting),
        ParserFor.make(RegexAtv2ExplanationEnabledSetting),
    ),
)
