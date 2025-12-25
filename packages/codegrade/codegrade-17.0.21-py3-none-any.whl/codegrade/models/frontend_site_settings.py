"""The module that defines the ``FrontendSiteSettings`` model.

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
from .fraction import Fraction


@dataclass
class FrontendSiteSettings:
    """The JSON representation of options visible to all users."""

    #: The default amount of time a step/substep in AutoTest can run. This can
    #: be overridden by the teacher.
    auto_test_max_time_command: Maybe[datetime.timedelta] = Nothing
    #: Default message for IO Test steps of an AutoTest.
    auto_test_io_test_message: Maybe[str] = Nothing
    #: Default message for IO Test sub-steps of an AutoTest.
    auto_test_io_test_sub_message: Maybe[str] = Nothing
    #: Default message for Run Program steps of an AutoTest.
    auto_test_run_program_message: Maybe[str] = Nothing
    #: Default message for Capture Points steps of an AutoTest.
    auto_test_capture_points_message: Maybe[str] = Nothing
    #: Default message for Checkpoint steps of an AutoTest.
    auto_test_checkpoint_message: Maybe[str] = Nothing
    #: Default message for Unit Test steps of an AutoTest.
    auto_test_unit_test_message: Maybe[str] = Nothing
    #: Default message for Code Quality steps of an AutoTest.
    auto_test_code_quality_message: Maybe[str] = Nothing
    #: The IDs of the currently recent base images for AutoTest 2.0. These are
    #: the images that we want users to use for new AutoTest 2.0
    #: configurations. Make sure that if you add something to this list it is
    #: also added to `NEW_AUTO_TEST_ALLOWED_INITIAL_BUILD_IDS`, as otherwise
    #: the user is not allowed to use the image. The last item in this list
    #: will be the default image id.
    new_auto_test_current_initial_build_ids: Maybe[t.Sequence[str]] = Nothing
    #: The maximum time a command may run in the build part of AutoTest 2.0.
    new_auto_test_build_max_command_time: Maybe[datetime.timedelta] = Nothing
    #: The maximum time a command may run in the test part of AutoTest 2.0.
    #: This is also the default value for timeout steps.
    new_auto_test_test_max_command_time: Maybe[datetime.timedelta] = Nothing
    #: Title for the output viewer in the code editor when we run the ATv2
    #: config.
    code_editor_output_viewer_title: Maybe[str] = Nothing
    #: The maximum time-delta an exam may take. Increasing this value also
    #: increases the maximum amount of time the login tokens send via email are
    #: valid. Therefore, you should make this too long.
    exam_login_max_length: Maybe[datetime.timedelta] = Nothing
    #: This determines how long before the exam we will send the login emails
    #: to the students (only when enabled of course).
    login_token_before_time: Maybe[t.Sequence[datetime.timedelta]] = Nothing
    #: The amount of time a reset token is valid. You should not increase this
    #: value too much as users might be not be too careful with these tokens.
    #: Increasing this value will allow **all** existing tokens to live longer.
    reset_token_time: Maybe[datetime.timedelta] = Nothing
    #: The email shown to users as the email of CodeGrade.
    site_email: Maybe[str] = Nothing
    #: The amount of time before an access token expires when we will show a
    #: toast message warning the user that their session is about to expire.
    access_token_toast_warning_time: Maybe[datetime.timedelta] = Nothing
    #: The amount of time before an access token expires when we will show a
    #: modal with a warning that the user's session is about to expire.
    access_token_modal_warning_time: Maybe[datetime.timedelta] = Nothing
    #: The maximum amount of lines that we should in render in one go. If a
    #: file contains more lines than this we will show a warning asking the
    #: user what to do.
    max_lines: Maybe[int] = Nothing
    #: The amount of time to wait between two consecutive polls to see if a
    #: user has new notifications. Setting this value too low will cause
    #: unnecessary stress on the server.
    notification_poll_time: Maybe[datetime.timedelta] = Nothing
    #: What is the maximum amount of time after a release a message should be
    #: shown on the HomeGrid. **Note**: this is the amount of time after the
    #: release, not after this instance has been upgraded to this release.
    release_message_max_time: Maybe[datetime.timedelta] = Nothing
    #: The maximum amount of matches of a plagiarism run that we will store. If
    #: there are more matches than this they will be discarded.
    max_plagiarism_matches: Maybe[int] = Nothing
    #: The maximum amount of time that the global setup script in AutoTest may
    #: take. If it takes longer than this it will be killed and the run will
    #: fail.
    auto_test_max_global_setup_time: Maybe[datetime.timedelta] = Nothing
    #: The maximum amount of time that the per student setup script in AutoTest
    #: may take. If it takes longer than this it will be killed and the result
    #: of the student will be in the state "timed-out".
    auto_test_max_per_student_setup_time: Maybe[datetime.timedelta] = Nothing
    #: The default value for the grading scale of new assignments.
    assignment_default_grading_scale: Maybe[
        t.Literal["percentage", "points"]
    ] = Nothing
    #: The default points grading scale points of new assignments.
    assignment_default_grading_scale_points: Maybe[Fraction] = Nothing
    #: If enabled teachers are allowed to bulk upload submissions (and create
    #: users) using a zip file in a format created by Blackboard.
    blackboard_zip_upload_enabled: Maybe[bool] = Nothing
    #: If enabled teachers can view rubrics on the submissions list page. Here
    #: they have the student view version of the rubric as apposed to the
    #: editor view in the manage assignment page.
    rubric_enabled_for_teacher_on_submissions_page: Maybe[bool] = Nothing
    #: Currently unused.
    automatic_lti_role_enabled: Maybe[bool] = Nothing
    #: Should it be possible to register on the website. This makes it possible
    #: for any body to register an account on the website.
    register_enabled: Maybe[bool] = Nothing
    #: Should group assignments be enabled.
    groups_enabled: Maybe[bool] = Nothing
    #: Should auto test be enabled.
    auto_test_enabled: Maybe[bool] = Nothing
    #: Should it be possible for teachers to create links that users can use to
    #: register in a course. Links to enroll can be created even if this
    #: feature is disabled.
    course_register_enabled: Maybe[bool] = Nothing
    #: Should it be possible to render html files within CodeGrade. This opens
    #: up more attack surfaces as it is now possible by design for students to
    #: run javascript. This is all done in a sandboxed iframe but still.
    render_html_enabled: Maybe[bool] = Nothing
    #: Should it be possible to email students.
    email_students_enabled: Maybe[bool] = Nothing
    #: Should peer feedback be enabled.
    peer_feedback_enabled: Maybe[bool] = Nothing
    #: Should AT image caching be enabled.
    at_image_caching_enabled: Maybe[bool] = Nothing
    #: Should it be possible to let students pay for a course. Please note that
    #: to enable this deploy config needs to be updated, so don't just enable
    #: it.
    student_payment_enabled: Maybe[bool] = Nothing
    #: Define what will be shown as the main option for student payment, the
    #: default will show stripe as the main payment option.
    student_payment_main_option: Maybe[t.Literal["coupon", "stripe"]] = Nothing
    #: Can students submit using the online editor.
    editor_enabled: Maybe[bool] = Nothing
    #: Whether the time as detected locally on a user's computer is corrected
    #: by the difference with the time as reported by the backend server.
    server_time_correction_enabled: Maybe[bool] = Nothing
    #: Whether teachers have access to the assignment manager - notifications
    #: panel, which gives control over when to send notifications to graders to
    #: finish their job, and also allows teachers to provide email(s) to notify
    #: when all graders are finished.
    grading_notifications_enabled: Maybe[bool] = Nothing
    #: Feedback threads will start collapsed from this depth of the tree.
    feedback_threads_initially_collapsed: Maybe[int] = Nothing
    #: The maximum amount of difference between the server time and the local
    #: time before we consider the local time to be out of sync with our
    #: servers.
    server_time_diff_tolerance: Maybe[datetime.timedelta] = Nothing
    #: The interval at which we request the server time in case it is out of
    #: sync with the local time.
    server_time_sync_interval: Maybe[datetime.timedelta] = Nothing
    #: Number of decimals for percentage-based grades in assignments, this also
    #: determines which decimal position the grade is rounded to.
    assignment_percentage_decimals: Maybe[int] = Nothing
    #: Number of decimals for point-based grades in assignments, this also
    #: determines which decimal position the grade is rounded to.
    assignment_point_decimals: Maybe[int] = Nothing
    #: How many lines of output we will still animate using the collapseable
    #: body in ATv2 output viewer.
    output_viewer_animation_limit_lines_count: Maybe[int] = Nothing
    #: How many steps in the failed state to expand automatically. Set to a
    #: negative value to automatically expand all steps.
    output_viewer_auto_expand_failed_steps: Maybe[int] = Nothing
    #: Should the lock date be copied from the LMS through LTI, or should we
    #: allow the user to set it in CodeGrade.
    lti_lock_date_copying_enabled: Maybe[bool] = Nothing
    #: Whether the "Max Points" field within the assignment general settings is
    #: enabled. If disabled, teachers will not be able to award extra points
    #: for assignments.
    assignment_max_points_enabled: Maybe[bool] = Nothing
    #: The minimum size of a gradebook before we show a warning that there are
    #: so many entries in the gradebook that it may slow down rendering or
    #: crash the page.
    course_gradebook_render_warning_size: Maybe[int] = Nothing
    #: Whether it is possible for teachers to create links for batches of users
    #: that can be used to register in a course. Links to enroll can be created
    #: even if this feature is disabled.
    course_bulk_register_enabled: Maybe[bool] = Nothing
    #: The file size above which users will be shown a warning that parsing the
    #: file might cause a slow down in their browser.
    csv_large_file_limit: Maybe[int] = Nothing
    #: The amount of errors that occur above which we will ask the user to make
    #: sure that the given file is actually a CSV.
    csv_too_many_errors_limit: Maybe[int] = Nothing
    #: The maximum age a submission can be before we do not retry subscribing
    #: to its result if it cannot be found the first time.
    new_auto_test_old_submission_age: Maybe[datetime.timedelta] = Nothing
    #: Should course id form Canvas be copied through LTI(1.3), and stored in
    #: our database or not.
    canvas_course_id_copying_enabled: Maybe[bool] = Nothing
    #: Whether the diff viewer should be shown in AutoTest v2 IO Test steps.
    new_auto_test_diff_viewer_enabled: Maybe[bool] = Nothing
    #: Whether to allow teachers to provide an URL of a GitHub repo, to be
    #: forked by the students when they setup a new repository via the GitHub
    #: integration.
    github_template_repo_enabled: Maybe[bool] = Nothing
    #: Whether the community library is enabled and available.
    community_library: Maybe[bool] = Nothing
    #: Whether it is possible to publish new items to the community library.
    #: This feature only has effect when `COMMUNITY_LIBRARY` is enabled too.
    community_library_publishing: Maybe[bool] = Nothing
    #: Whether quality comments generated by code editor ATv2 runs should be
    #: displayed in the editor.
    quality_comments_in_code_editor: Maybe[bool] = Nothing
    #: Whether during an SSO launch new user are granted their global role
    #: based on the SSO launch data.
    sso_infer_global_staff_role: Maybe[bool] = Nothing
    #: The amount of time that the step will run before its output will
    #: automatically uncollapse in the output viewer unless the user has
    #: toggled the collapse themselves.
    new_auto_test_uncollapsing_step_output_delay: Maybe[datetime.timedelta] = (
        Nothing
    )
    #: Whether to show the assignment description on the submissions page for
    #: teachers.
    assignment_description_on_teachers_submissions_page: Maybe[bool] = Nothing
    #: Whether the submission rubric viewer uses inline when the tab view does
    #: not fit. On the submission page we show the rubric viewer that will
    #: allow the teacher to fill in the rubric and the student to view their
    #: score in the different categories. With this feature enabled, we
    #: calculate whether all of the categories fit on a single line, and
    #: otherwise use a dropdown with previous and next buttons to select
    #: categories.
    inline_rubric_viewer_enabled: Maybe[bool] = Nothing
    #: Whether we will hide all of the steps in the code editor sidebar output
    #: viewer if we have in a quiz-only atv2 config.
    hide_code_editor_output_viewer_with_only_quiz_steps: Maybe[bool] = Nothing
    #: Whether we will hide the buttons to add a file and a directory in the
    #: code editor, if we have a quiz-only atv2 config.
    hide_code_editor_filetree_controls_with_only_quiz_steps: Maybe[bool] = (
        Nothing
    )
    #: Whether we update the simple submission mode navigation to check if we
    #: have an editor session which is later than the submission when we launch
    #: the assignment. This feature is only available when the simple
    #: submission mode is enabled. Be mindful of turning this on when the
    #: tenant uses deadlines.
    simple_submission_navigate_to_latest_editor_session: Maybe[bool] = Nothing
    #: Whether we should show the grades of submissions created within this
    #: tenant. This will not hide the rubric results, only the grades. This is
    #: meant to be used with LTI providers that apply penalties (for example
    #: when handing in late) outside of CodeGrade.
    display_grades_enabled: Maybe[bool] = Nothing
    #: Whether we hide the rubric row description space in the rubric viewer if
    #: the description is empty.
    hide_empty_rubric_row_description: Maybe[bool] = Nothing
    #: The default tab to select when going to a submission.
    default_submission_page_tab: Maybe[
        t.Literal[
            "auto-test", "code", "feedback-overview", "peer-feedback", "smart"
        ]
    ] = Nothing
    #: Should we hide the "No deadline" message if no deadline or lock date is
    #: set.
    hide_no_deadline_enabled: Maybe[bool] = Nothing
    #: Should we retry passing back grades for group submissions when the
    #: passback request failed for some but not all of the group members.
    retry_group_submission_grade_passback_enabled: Maybe[bool] = Nothing
    #: Whether to open the assignment description as the first file in the Code
    #: Editor, if the assignment has one, or the first file in the file tree.
    code_editor_start_on_assignment_description: Maybe[bool] = Nothing
    #: The main feature flag for all the AI assistant capabilities in
    #: codegrade, whether we enable the ai assistant to be inside the app.
    ai_assistant_enabled: Maybe[bool] = Nothing
    #: Whether the AI assistant in the app has access to tools to retrieve more
    #: information through requesting tool use while conversing with a user.
    assistant_tools_enabled: Maybe[bool] = Nothing
    #: The main feature flag for the ATv2 prompt engineering step. If enabled
    #: the step will be available within the AutoTestv2 editor.
    prompt_engineering_step_enabled: Maybe[bool] = Nothing
    #: Whether to get the first day of the week in calendars from the user's
    #: configured locale. If disabled the first day of the week will default to
    #: Sunday.
    first_day_of_week_from_locale: Maybe[bool] = Nothing
    #: Whether to allow giving inline feedback on quiz questions.
    inline_feedback_on_quizzes_enabled: Maybe[bool] = Nothing
    #: Whether to hide the "▶️ Run" button in the editor sidebar when an
    #: assignment contains only quizzes with the "Run single questions" feature
    #: enabled.
    quiz_single_question_mode_hide_run_button_enabled: Maybe[bool] = Nothing
    #: Whether we are allowed to display the warning for missing newlines in
    #: the code viewer. If we set disable this feature, passing the property to
    #: show the warning will be overridden and the warning will *never* show.
    warning_for_missing_newline_enabled: Maybe[bool] = Nothing
    #: Whether the Jupyter Notebook editor is enabled in the Code Editor. Note:
    #: after disabling this feature, existing Jupyter Notebooks will still
    #: continue to use the Jupyter Notebook editor.
    jupyter_notebook_editor_enabled: Maybe[bool] = Nothing
    #: Whether the Jupyter Notebook can be run in the Code Editor. Note:
    #: Disabling this feature does not prevent Jupyter Notebooks from being
    #: viewed. For that, see the JUPYTER_NOTEBOOK_EDITOR_ENABLED site setting.
    jupyter_notebook_running_enabled: Maybe[bool] = Nothing
    #: Enables an action while answering a coding question, in the editor, to
    #: reset your answer to the question entirely. When triggered, the editor
    #: will revert to the starter code and mark the question as unanswered. Use
    #: with caution—especially for graded questions—as this could cause
    #: permanent loss of work, should the user leave the page before reverting
    #: the complete reset.
    coding_question_editor_reset_answer_enabled: Maybe[bool] = Nothing
    #: Allow quiz authors to configure a reference solution on coding
    #: questions. When enabled, quiz-takers can compare their code against the
    #: ATv2 reference implementation. During the quiz, users with permission
    #: will see an action on coding questions that reveals the configured
    #: solution.
    coding_question_solution_enabled: Maybe[bool] = Nothing
    #: Allows users to download files from those listed in the file tree within
    #: the code editor. This includes quizzes, Jupyter Notebooks, images, code
    #: and other files which can be viewed as text.
    download_editor_files_enabled: Maybe[bool] = Nothing
    #: Whether to allow teachers to enable single page quizzes. In a single
    #: page quiz all questions are rendered below each other on a single,
    #: scrollable page.
    quiz_view_modes_enabled: Maybe[bool] = Nothing
    #: Whether we should show a explanation and regex example for regex match
    #: steps.
    regex_atv2_explanation_enabled: Maybe[bool] = Nothing

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: rqa.FixedMapping(
            rqa.OptionalArgument(
                "AUTO_TEST_MAX_TIME_COMMAND",
                rqa.RichValue.TimeDelta,
                doc="The default amount of time a step/substep in AutoTest can run. This can be overridden by the teacher.",
            ),
            rqa.OptionalArgument(
                "AUTO_TEST_IO_TEST_MESSAGE",
                rqa.SimpleValue.str,
                doc="Default message for IO Test steps of an AutoTest.",
            ),
            rqa.OptionalArgument(
                "AUTO_TEST_IO_TEST_SUB_MESSAGE",
                rqa.SimpleValue.str,
                doc="Default message for IO Test sub-steps of an AutoTest.",
            ),
            rqa.OptionalArgument(
                "AUTO_TEST_RUN_PROGRAM_MESSAGE",
                rqa.SimpleValue.str,
                doc="Default message for Run Program steps of an AutoTest.",
            ),
            rqa.OptionalArgument(
                "AUTO_TEST_CAPTURE_POINTS_MESSAGE",
                rqa.SimpleValue.str,
                doc="Default message for Capture Points steps of an AutoTest.",
            ),
            rqa.OptionalArgument(
                "AUTO_TEST_CHECKPOINT_MESSAGE",
                rqa.SimpleValue.str,
                doc="Default message for Checkpoint steps of an AutoTest.",
            ),
            rqa.OptionalArgument(
                "AUTO_TEST_UNIT_TEST_MESSAGE",
                rqa.SimpleValue.str,
                doc="Default message for Unit Test steps of an AutoTest.",
            ),
            rqa.OptionalArgument(
                "AUTO_TEST_CODE_QUALITY_MESSAGE",
                rqa.SimpleValue.str,
                doc="Default message for Code Quality steps of an AutoTest.",
            ),
            rqa.OptionalArgument(
                "NEW_AUTO_TEST_CURRENT_INITIAL_BUILD_IDS",
                rqa.List(rqa.SimpleValue.str),
                doc="The IDs of the currently recent base images for AutoTest 2.0. These are the images that we want users to use for new AutoTest 2.0 configurations. Make sure that if you add something to this list it is also added to `NEW_AUTO_TEST_ALLOWED_INITIAL_BUILD_IDS`, as otherwise the user is not allowed to use the image. The last item in this list will be the default image id.",
            ),
            rqa.OptionalArgument(
                "NEW_AUTO_TEST_BUILD_MAX_COMMAND_TIME",
                rqa.RichValue.TimeDelta,
                doc="The maximum time a command may run in the build part of AutoTest 2.0.",
            ),
            rqa.OptionalArgument(
                "NEW_AUTO_TEST_TEST_MAX_COMMAND_TIME",
                rqa.RichValue.TimeDelta,
                doc="The maximum time a command may run in the test part of AutoTest 2.0. This is also the default value for timeout steps.",
            ),
            rqa.OptionalArgument(
                "CODE_EDITOR_OUTPUT_VIEWER_TITLE",
                rqa.SimpleValue.str,
                doc="Title for the output viewer in the code editor when we run the ATv2 config.",
            ),
            rqa.OptionalArgument(
                "EXAM_LOGIN_MAX_LENGTH",
                rqa.RichValue.TimeDelta,
                doc="The maximum time-delta an exam may take. Increasing this value also increases the maximum amount of time the login tokens send via email are valid. Therefore, you should make this too long.",
            ),
            rqa.OptionalArgument(
                "LOGIN_TOKEN_BEFORE_TIME",
                rqa.List(rqa.RichValue.TimeDelta),
                doc="This determines how long before the exam we will send the login emails to the students (only when enabled of course).",
            ),
            rqa.OptionalArgument(
                "RESET_TOKEN_TIME",
                rqa.RichValue.TimeDelta,
                doc="The amount of time a reset token is valid. You should not increase this value too much as users might be not be too careful with these tokens. Increasing this value will allow **all** existing tokens to live longer.",
            ),
            rqa.OptionalArgument(
                "SITE_EMAIL",
                rqa.SimpleValue.str,
                doc="The email shown to users as the email of CodeGrade.",
            ),
            rqa.OptionalArgument(
                "ACCESS_TOKEN_TOAST_WARNING_TIME",
                rqa.RichValue.TimeDelta,
                doc="The amount of time before an access token expires when we will show a toast message warning the user that their session is about to expire.",
            ),
            rqa.OptionalArgument(
                "ACCESS_TOKEN_MODAL_WARNING_TIME",
                rqa.RichValue.TimeDelta,
                doc="The amount of time before an access token expires when we will show a modal with a warning that the user's session is about to expire.",
            ),
            rqa.OptionalArgument(
                "MAX_LINES",
                rqa.SimpleValue.int,
                doc="The maximum amount of lines that we should in render in one go. If a file contains more lines than this we will show a warning asking the user what to do.",
            ),
            rqa.OptionalArgument(
                "NOTIFICATION_POLL_TIME",
                rqa.RichValue.TimeDelta,
                doc="The amount of time to wait between two consecutive polls to see if a user has new notifications. Setting this value too low will cause unnecessary stress on the server.",
            ),
            rqa.OptionalArgument(
                "RELEASE_MESSAGE_MAX_TIME",
                rqa.RichValue.TimeDelta,
                doc="What is the maximum amount of time after a release a message should be shown on the HomeGrid. **Note**: this is the amount of time after the release, not after this instance has been upgraded to this release.",
            ),
            rqa.OptionalArgument(
                "MAX_PLAGIARISM_MATCHES",
                rqa.SimpleValue.int,
                doc="The maximum amount of matches of a plagiarism run that we will store. If there are more matches than this they will be discarded.",
            ),
            rqa.OptionalArgument(
                "AUTO_TEST_MAX_GLOBAL_SETUP_TIME",
                rqa.RichValue.TimeDelta,
                doc="The maximum amount of time that the global setup script in AutoTest may take. If it takes longer than this it will be killed and the run will fail.",
            ),
            rqa.OptionalArgument(
                "AUTO_TEST_MAX_PER_STUDENT_SETUP_TIME",
                rqa.RichValue.TimeDelta,
                doc='The maximum amount of time that the per student setup script in AutoTest may take. If it takes longer than this it will be killed and the result of the student will be in the state "timed-out".',
            ),
            rqa.OptionalArgument(
                "ASSIGNMENT_DEFAULT_GRADING_SCALE",
                rqa.StringEnum("percentage", "points"),
                doc="The default value for the grading scale of new assignments.",
            ),
            rqa.OptionalArgument(
                "ASSIGNMENT_DEFAULT_GRADING_SCALE_POINTS",
                parsers.ParserFor.make(Fraction),
                doc="The default points grading scale points of new assignments.",
            ),
            rqa.OptionalArgument(
                "BLACKBOARD_ZIP_UPLOAD_ENABLED",
                rqa.SimpleValue.bool,
                doc="If enabled teachers are allowed to bulk upload submissions (and create users) using a zip file in a format created by Blackboard.",
            ),
            rqa.OptionalArgument(
                "RUBRIC_ENABLED_FOR_TEACHER_ON_SUBMISSIONS_PAGE",
                rqa.SimpleValue.bool,
                doc="If enabled teachers can view rubrics on the submissions list page. Here they have the student view version of the rubric as apposed to the editor view in the manage assignment page.",
            ),
            rqa.OptionalArgument(
                "AUTOMATIC_LTI_ROLE_ENABLED",
                rqa.SimpleValue.bool,
                doc="Currently unused.",
            ),
            rqa.OptionalArgument(
                "REGISTER_ENABLED",
                rqa.SimpleValue.bool,
                doc="Should it be possible to register on the website. This makes it possible for any body to register an account on the website.",
            ),
            rqa.OptionalArgument(
                "GROUPS_ENABLED",
                rqa.SimpleValue.bool,
                doc="Should group assignments be enabled.",
            ),
            rqa.OptionalArgument(
                "AUTO_TEST_ENABLED",
                rqa.SimpleValue.bool,
                doc="Should auto test be enabled.",
            ),
            rqa.OptionalArgument(
                "COURSE_REGISTER_ENABLED",
                rqa.SimpleValue.bool,
                doc="Should it be possible for teachers to create links that users can use to register in a course. Links to enroll can be created even if this feature is disabled.",
            ),
            rqa.OptionalArgument(
                "RENDER_HTML_ENABLED",
                rqa.SimpleValue.bool,
                doc="Should it be possible to render html files within CodeGrade. This opens up more attack surfaces as it is now possible by design for students to run javascript. This is all done in a sandboxed iframe but still.",
            ),
            rqa.OptionalArgument(
                "EMAIL_STUDENTS_ENABLED",
                rqa.SimpleValue.bool,
                doc="Should it be possible to email students.",
            ),
            rqa.OptionalArgument(
                "PEER_FEEDBACK_ENABLED",
                rqa.SimpleValue.bool,
                doc="Should peer feedback be enabled.",
            ),
            rqa.OptionalArgument(
                "AT_IMAGE_CACHING_ENABLED",
                rqa.SimpleValue.bool,
                doc="Should AT image caching be enabled.",
            ),
            rqa.OptionalArgument(
                "STUDENT_PAYMENT_ENABLED",
                rqa.SimpleValue.bool,
                doc="Should it be possible to let students pay for a course. Please note that to enable this deploy config needs to be updated, so don't just enable it.",
            ),
            rqa.OptionalArgument(
                "STUDENT_PAYMENT_MAIN_OPTION",
                rqa.StringEnum("coupon", "stripe"),
                doc="Define what will be shown as the main option for student payment, the default will show stripe as the main payment option.",
            ),
            rqa.OptionalArgument(
                "EDITOR_ENABLED",
                rqa.SimpleValue.bool,
                doc="Can students submit using the online editor.",
            ),
            rqa.OptionalArgument(
                "SERVER_TIME_CORRECTION_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether the time as detected locally on a user's computer is corrected by the difference with the time as reported by the backend server.",
            ),
            rqa.OptionalArgument(
                "GRADING_NOTIFICATIONS_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether teachers have access to the assignment manager - notifications panel, which gives control over when to send notifications to graders to finish their job, and also allows teachers to provide email(s) to notify when all graders are finished.",
            ),
            rqa.OptionalArgument(
                "FEEDBACK_THREADS_INITIALLY_COLLAPSED",
                rqa.SimpleValue.int,
                doc="Feedback threads will start collapsed from this depth of the tree.",
            ),
            rqa.OptionalArgument(
                "SERVER_TIME_DIFF_TOLERANCE",
                rqa.RichValue.TimeDelta,
                doc="The maximum amount of difference between the server time and the local time before we consider the local time to be out of sync with our servers.",
            ),
            rqa.OptionalArgument(
                "SERVER_TIME_SYNC_INTERVAL",
                rqa.RichValue.TimeDelta,
                doc="The interval at which we request the server time in case it is out of sync with the local time.",
            ),
            rqa.OptionalArgument(
                "ASSIGNMENT_PERCENTAGE_DECIMALS",
                rqa.SimpleValue.int,
                doc="Number of decimals for percentage-based grades in assignments, this also determines which decimal position the grade is rounded to.",
            ),
            rqa.OptionalArgument(
                "ASSIGNMENT_POINT_DECIMALS",
                rqa.SimpleValue.int,
                doc="Number of decimals for point-based grades in assignments, this also determines which decimal position the grade is rounded to.",
            ),
            rqa.OptionalArgument(
                "OUTPUT_VIEWER_ANIMATION_LIMIT_LINES_COUNT",
                rqa.SimpleValue.int,
                doc="How many lines of output we will still animate using the collapseable body in ATv2 output viewer.",
            ),
            rqa.OptionalArgument(
                "OUTPUT_VIEWER_AUTO_EXPAND_FAILED_STEPS",
                rqa.SimpleValue.int,
                doc="How many steps in the failed state to expand automatically. Set to a negative value to automatically expand all steps.",
            ),
            rqa.OptionalArgument(
                "LTI_LOCK_DATE_COPYING_ENABLED",
                rqa.SimpleValue.bool,
                doc="Should the lock date be copied from the LMS through LTI, or should we allow the user to set it in CodeGrade.",
            ),
            rqa.OptionalArgument(
                "ASSIGNMENT_MAX_POINTS_ENABLED",
                rqa.SimpleValue.bool,
                doc='Whether the "Max Points" field within the assignment general settings is enabled. If disabled, teachers will not be able to award extra points for assignments.',
            ),
            rqa.OptionalArgument(
                "COURSE_GRADEBOOK_RENDER_WARNING_SIZE",
                rqa.SimpleValue.int,
                doc="The minimum size of a gradebook before we show a warning that there are so many entries in the gradebook that it may slow down rendering or crash the page.",
            ),
            rqa.OptionalArgument(
                "COURSE_BULK_REGISTER_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether it is possible for teachers to create links for batches of users that can be used to register in a course. Links to enroll can be created even if this feature is disabled.",
            ),
            rqa.OptionalArgument(
                "CSV_LARGE_FILE_LIMIT",
                rqa.SimpleValue.int,
                doc="The file size above which users will be shown a warning that parsing the file might cause a slow down in their browser.",
            ),
            rqa.OptionalArgument(
                "CSV_TOO_MANY_ERRORS_LIMIT",
                rqa.SimpleValue.int,
                doc="The amount of errors that occur above which we will ask the user to make sure that the given file is actually a CSV.",
            ),
            rqa.OptionalArgument(
                "NEW_AUTO_TEST_OLD_SUBMISSION_AGE",
                rqa.RichValue.TimeDelta,
                doc="The maximum age a submission can be before we do not retry subscribing to its result if it cannot be found the first time.",
            ),
            rqa.OptionalArgument(
                "CANVAS_COURSE_ID_COPYING_ENABLED",
                rqa.SimpleValue.bool,
                doc="Should course id form Canvas be copied through LTI(1.3), and stored in our database or not.",
            ),
            rqa.OptionalArgument(
                "NEW_AUTO_TEST_DIFF_VIEWER_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether the diff viewer should be shown in AutoTest v2 IO Test steps.",
            ),
            rqa.OptionalArgument(
                "GITHUB_TEMPLATE_REPO_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether to allow teachers to provide an URL of a GitHub repo, to be forked by the students when they setup a new repository via the GitHub integration.",
            ),
            rqa.OptionalArgument(
                "COMMUNITY_LIBRARY",
                rqa.SimpleValue.bool,
                doc="Whether the community library is enabled and available.",
            ),
            rqa.OptionalArgument(
                "COMMUNITY_LIBRARY_PUBLISHING",
                rqa.SimpleValue.bool,
                doc="Whether it is possible to publish new items to the community library. This feature only has effect when `COMMUNITY_LIBRARY` is enabled too.",
            ),
            rqa.OptionalArgument(
                "QUALITY_COMMENTS_IN_CODE_EDITOR",
                rqa.SimpleValue.bool,
                doc="Whether quality comments generated by code editor ATv2 runs should be displayed in the editor.",
            ),
            rqa.OptionalArgument(
                "SSO_INFER_GLOBAL_STAFF_ROLE",
                rqa.SimpleValue.bool,
                doc="Whether during an SSO launch new user are granted their global role based on the SSO launch data.",
            ),
            rqa.OptionalArgument(
                "NEW_AUTO_TEST_UNCOLLAPSING_STEP_OUTPUT_DELAY",
                rqa.RichValue.TimeDelta,
                doc="The amount of time that the step will run before its output will automatically uncollapse in the output viewer unless the user has toggled the collapse themselves.",
            ),
            rqa.OptionalArgument(
                "ASSIGNMENT_DESCRIPTION_ON_TEACHERS_SUBMISSIONS_PAGE",
                rqa.SimpleValue.bool,
                doc="Whether to show the assignment description on the submissions page for teachers.",
            ),
            rqa.OptionalArgument(
                "INLINE_RUBRIC_VIEWER_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether the submission rubric viewer uses inline when the tab view does not fit. On the submission page we show the rubric viewer that will allow the teacher to fill in the rubric and the student to view their score in the different categories. With this feature enabled, we calculate whether all of the categories fit on a single line, and otherwise use a dropdown with previous and next buttons to select categories.",
            ),
            rqa.OptionalArgument(
                "HIDE_CODE_EDITOR_OUTPUT_VIEWER_WITH_ONLY_QUIZ_STEPS",
                rqa.SimpleValue.bool,
                doc="Whether we will hide all of the steps in the code editor sidebar output viewer if we have in a quiz-only atv2 config.",
            ),
            rqa.OptionalArgument(
                "HIDE_CODE_EDITOR_FILETREE_CONTROLS_WITH_ONLY_QUIZ_STEPS",
                rqa.SimpleValue.bool,
                doc="Whether we will hide the buttons to add a file and a directory in the code editor, if we have a quiz-only atv2 config.",
            ),
            rqa.OptionalArgument(
                "SIMPLE_SUBMISSION_NAVIGATE_TO_LATEST_EDITOR_SESSION",
                rqa.SimpleValue.bool,
                doc="Whether we update the simple submission mode navigation to check if we have an editor session which is later than the submission when we launch the assignment. This feature is only available when the simple submission mode is enabled. Be mindful of turning this on when the tenant uses deadlines.",
            ),
            rqa.OptionalArgument(
                "DISPLAY_GRADES_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether we should show the grades of submissions created within this tenant. This will not hide the rubric results, only the grades. This is meant to be used with LTI providers that apply penalties (for example when handing in late) outside of CodeGrade.",
            ),
            rqa.OptionalArgument(
                "HIDE_EMPTY_RUBRIC_ROW_DESCRIPTION",
                rqa.SimpleValue.bool,
                doc="Whether we hide the rubric row description space in the rubric viewer if the description is empty.",
            ),
            rqa.OptionalArgument(
                "DEFAULT_SUBMISSION_PAGE_TAB",
                rqa.StringEnum(
                    "auto-test",
                    "code",
                    "feedback-overview",
                    "peer-feedback",
                    "smart",
                ),
                doc="The default tab to select when going to a submission.",
            ),
            rqa.OptionalArgument(
                "HIDE_NO_DEADLINE_ENABLED",
                rqa.SimpleValue.bool,
                doc='Should we hide the "No deadline" message if no deadline or lock date is set.',
            ),
            rqa.OptionalArgument(
                "RETRY_GROUP_SUBMISSION_GRADE_PASSBACK_ENABLED",
                rqa.SimpleValue.bool,
                doc="Should we retry passing back grades for group submissions when the passback request failed for some but not all of the group members.",
            ),
            rqa.OptionalArgument(
                "CODE_EDITOR_START_ON_ASSIGNMENT_DESCRIPTION",
                rqa.SimpleValue.bool,
                doc="Whether to open the assignment description as the first file in the Code Editor, if the assignment has one, or the first file in the file tree.",
            ),
            rqa.OptionalArgument(
                "AI_ASSISTANT_ENABLED",
                rqa.SimpleValue.bool,
                doc="The main feature flag for all the AI assistant capabilities in codegrade, whether we enable the ai assistant to be inside the app.",
            ),
            rqa.OptionalArgument(
                "ASSISTANT_TOOLS_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether the AI assistant in the app has access to tools to retrieve more information through requesting tool use while conversing with a user.",
            ),
            rqa.OptionalArgument(
                "PROMPT_ENGINEERING_STEP_ENABLED",
                rqa.SimpleValue.bool,
                doc="The main feature flag for the ATv2 prompt engineering step. If enabled the step will be available within the AutoTestv2 editor.",
            ),
            rqa.OptionalArgument(
                "FIRST_DAY_OF_WEEK_FROM_LOCALE",
                rqa.SimpleValue.bool,
                doc="Whether to get the first day of the week in calendars from the user's configured locale. If disabled the first day of the week will default to Sunday.",
            ),
            rqa.OptionalArgument(
                "INLINE_FEEDBACK_ON_QUIZZES_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether to allow giving inline feedback on quiz questions.",
            ),
            rqa.OptionalArgument(
                "QUIZ_SINGLE_QUESTION_MODE_HIDE_RUN_BUTTON_ENABLED",
                rqa.SimpleValue.bool,
                doc='Whether to hide the "▶️ Run" button in the editor sidebar when an assignment contains only quizzes with the "Run single questions" feature enabled.',
            ),
            rqa.OptionalArgument(
                "WARNING_FOR_MISSING_NEWLINE_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether we are allowed to display the warning for missing newlines in the code viewer. If we set disable this feature, passing the property to show the warning will be overridden and the warning will *never* show.",
            ),
            rqa.OptionalArgument(
                "JUPYTER_NOTEBOOK_EDITOR_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether the Jupyter Notebook editor is enabled in the Code Editor. Note: after disabling this feature, existing Jupyter Notebooks will still continue to use the Jupyter Notebook editor.",
            ),
            rqa.OptionalArgument(
                "JUPYTER_NOTEBOOK_RUNNING_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether the Jupyter Notebook can be run in the Code Editor. Note: Disabling this feature does not prevent Jupyter Notebooks from being viewed. For that, see the JUPYTER_NOTEBOOK_EDITOR_ENABLED site setting.",
            ),
            rqa.OptionalArgument(
                "CODING_QUESTION_EDITOR_RESET_ANSWER_ENABLED",
                rqa.SimpleValue.bool,
                doc="Enables an action while answering a coding question, in the editor, to reset your answer to the question entirely. When triggered, the editor will revert to the starter code and mark the question as unanswered. Use with caution—especially for graded questions—as this could cause permanent loss of work, should the user leave the page before reverting the complete reset.",
            ),
            rqa.OptionalArgument(
                "CODING_QUESTION_SOLUTION_ENABLED",
                rqa.SimpleValue.bool,
                doc="Allow quiz authors to configure a reference solution on coding questions. When enabled, quiz-takers can compare their code against the ATv2 reference implementation. During the quiz, users with permission will see an action on coding questions that reveals the configured solution.",
            ),
            rqa.OptionalArgument(
                "DOWNLOAD_EDITOR_FILES_ENABLED",
                rqa.SimpleValue.bool,
                doc="Allows users to download files from those listed in the file tree within the code editor. This includes quizzes, Jupyter Notebooks, images, code and other files which can be viewed as text.",
            ),
            rqa.OptionalArgument(
                "QUIZ_VIEW_MODES_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether to allow teachers to enable single page quizzes. In a single page quiz all questions are rendered below each other on a single, scrollable page.",
            ),
            rqa.OptionalArgument(
                "REGEX_ATV2_EXPLANATION_ENABLED",
                rqa.SimpleValue.bool,
                doc="Whether we should show a explanation and regex example for regex match steps.",
            ),
        ).use_readable_describe(True)
    )

    def __post_init__(self) -> None:
        getattr(super(), "__post_init__", lambda: None)()
        self.auto_test_max_time_command = maybe_from_nullable(
            self.auto_test_max_time_command
        )
        self.auto_test_io_test_message = maybe_from_nullable(
            self.auto_test_io_test_message
        )
        self.auto_test_io_test_sub_message = maybe_from_nullable(
            self.auto_test_io_test_sub_message
        )
        self.auto_test_run_program_message = maybe_from_nullable(
            self.auto_test_run_program_message
        )
        self.auto_test_capture_points_message = maybe_from_nullable(
            self.auto_test_capture_points_message
        )
        self.auto_test_checkpoint_message = maybe_from_nullable(
            self.auto_test_checkpoint_message
        )
        self.auto_test_unit_test_message = maybe_from_nullable(
            self.auto_test_unit_test_message
        )
        self.auto_test_code_quality_message = maybe_from_nullable(
            self.auto_test_code_quality_message
        )
        self.new_auto_test_current_initial_build_ids = maybe_from_nullable(
            self.new_auto_test_current_initial_build_ids
        )
        self.new_auto_test_build_max_command_time = maybe_from_nullable(
            self.new_auto_test_build_max_command_time
        )
        self.new_auto_test_test_max_command_time = maybe_from_nullable(
            self.new_auto_test_test_max_command_time
        )
        self.code_editor_output_viewer_title = maybe_from_nullable(
            self.code_editor_output_viewer_title
        )
        self.exam_login_max_length = maybe_from_nullable(
            self.exam_login_max_length
        )
        self.login_token_before_time = maybe_from_nullable(
            self.login_token_before_time
        )
        self.reset_token_time = maybe_from_nullable(self.reset_token_time)
        self.site_email = maybe_from_nullable(self.site_email)
        self.access_token_toast_warning_time = maybe_from_nullable(
            self.access_token_toast_warning_time
        )
        self.access_token_modal_warning_time = maybe_from_nullable(
            self.access_token_modal_warning_time
        )
        self.max_lines = maybe_from_nullable(self.max_lines)
        self.notification_poll_time = maybe_from_nullable(
            self.notification_poll_time
        )
        self.release_message_max_time = maybe_from_nullable(
            self.release_message_max_time
        )
        self.max_plagiarism_matches = maybe_from_nullable(
            self.max_plagiarism_matches
        )
        self.auto_test_max_global_setup_time = maybe_from_nullable(
            self.auto_test_max_global_setup_time
        )
        self.auto_test_max_per_student_setup_time = maybe_from_nullable(
            self.auto_test_max_per_student_setup_time
        )
        self.assignment_default_grading_scale = maybe_from_nullable(
            self.assignment_default_grading_scale
        )
        self.assignment_default_grading_scale_points = maybe_from_nullable(
            self.assignment_default_grading_scale_points
        )
        self.blackboard_zip_upload_enabled = maybe_from_nullable(
            self.blackboard_zip_upload_enabled
        )
        self.rubric_enabled_for_teacher_on_submissions_page = (
            maybe_from_nullable(
                self.rubric_enabled_for_teacher_on_submissions_page
            )
        )
        self.automatic_lti_role_enabled = maybe_from_nullable(
            self.automatic_lti_role_enabled
        )
        self.register_enabled = maybe_from_nullable(self.register_enabled)
        self.groups_enabled = maybe_from_nullable(self.groups_enabled)
        self.auto_test_enabled = maybe_from_nullable(self.auto_test_enabled)
        self.course_register_enabled = maybe_from_nullable(
            self.course_register_enabled
        )
        self.render_html_enabled = maybe_from_nullable(
            self.render_html_enabled
        )
        self.email_students_enabled = maybe_from_nullable(
            self.email_students_enabled
        )
        self.peer_feedback_enabled = maybe_from_nullable(
            self.peer_feedback_enabled
        )
        self.at_image_caching_enabled = maybe_from_nullable(
            self.at_image_caching_enabled
        )
        self.student_payment_enabled = maybe_from_nullable(
            self.student_payment_enabled
        )
        self.student_payment_main_option = maybe_from_nullable(
            self.student_payment_main_option
        )
        self.editor_enabled = maybe_from_nullable(self.editor_enabled)
        self.server_time_correction_enabled = maybe_from_nullable(
            self.server_time_correction_enabled
        )
        self.grading_notifications_enabled = maybe_from_nullable(
            self.grading_notifications_enabled
        )
        self.feedback_threads_initially_collapsed = maybe_from_nullable(
            self.feedback_threads_initially_collapsed
        )
        self.server_time_diff_tolerance = maybe_from_nullable(
            self.server_time_diff_tolerance
        )
        self.server_time_sync_interval = maybe_from_nullable(
            self.server_time_sync_interval
        )
        self.assignment_percentage_decimals = maybe_from_nullable(
            self.assignment_percentage_decimals
        )
        self.assignment_point_decimals = maybe_from_nullable(
            self.assignment_point_decimals
        )
        self.output_viewer_animation_limit_lines_count = maybe_from_nullable(
            self.output_viewer_animation_limit_lines_count
        )
        self.output_viewer_auto_expand_failed_steps = maybe_from_nullable(
            self.output_viewer_auto_expand_failed_steps
        )
        self.lti_lock_date_copying_enabled = maybe_from_nullable(
            self.lti_lock_date_copying_enabled
        )
        self.assignment_max_points_enabled = maybe_from_nullable(
            self.assignment_max_points_enabled
        )
        self.course_gradebook_render_warning_size = maybe_from_nullable(
            self.course_gradebook_render_warning_size
        )
        self.course_bulk_register_enabled = maybe_from_nullable(
            self.course_bulk_register_enabled
        )
        self.csv_large_file_limit = maybe_from_nullable(
            self.csv_large_file_limit
        )
        self.csv_too_many_errors_limit = maybe_from_nullable(
            self.csv_too_many_errors_limit
        )
        self.new_auto_test_old_submission_age = maybe_from_nullable(
            self.new_auto_test_old_submission_age
        )
        self.canvas_course_id_copying_enabled = maybe_from_nullable(
            self.canvas_course_id_copying_enabled
        )
        self.new_auto_test_diff_viewer_enabled = maybe_from_nullable(
            self.new_auto_test_diff_viewer_enabled
        )
        self.github_template_repo_enabled = maybe_from_nullable(
            self.github_template_repo_enabled
        )
        self.community_library = maybe_from_nullable(self.community_library)
        self.community_library_publishing = maybe_from_nullable(
            self.community_library_publishing
        )
        self.quality_comments_in_code_editor = maybe_from_nullable(
            self.quality_comments_in_code_editor
        )
        self.sso_infer_global_staff_role = maybe_from_nullable(
            self.sso_infer_global_staff_role
        )
        self.new_auto_test_uncollapsing_step_output_delay = (
            maybe_from_nullable(
                self.new_auto_test_uncollapsing_step_output_delay
            )
        )
        self.assignment_description_on_teachers_submissions_page = (
            maybe_from_nullable(
                self.assignment_description_on_teachers_submissions_page
            )
        )
        self.inline_rubric_viewer_enabled = maybe_from_nullable(
            self.inline_rubric_viewer_enabled
        )
        self.hide_code_editor_output_viewer_with_only_quiz_steps = (
            maybe_from_nullable(
                self.hide_code_editor_output_viewer_with_only_quiz_steps
            )
        )
        self.hide_code_editor_filetree_controls_with_only_quiz_steps = (
            maybe_from_nullable(
                self.hide_code_editor_filetree_controls_with_only_quiz_steps
            )
        )
        self.simple_submission_navigate_to_latest_editor_session = (
            maybe_from_nullable(
                self.simple_submission_navigate_to_latest_editor_session
            )
        )
        self.display_grades_enabled = maybe_from_nullable(
            self.display_grades_enabled
        )
        self.hide_empty_rubric_row_description = maybe_from_nullable(
            self.hide_empty_rubric_row_description
        )
        self.default_submission_page_tab = maybe_from_nullable(
            self.default_submission_page_tab
        )
        self.hide_no_deadline_enabled = maybe_from_nullable(
            self.hide_no_deadline_enabled
        )
        self.retry_group_submission_grade_passback_enabled = (
            maybe_from_nullable(
                self.retry_group_submission_grade_passback_enabled
            )
        )
        self.code_editor_start_on_assignment_description = maybe_from_nullable(
            self.code_editor_start_on_assignment_description
        )
        self.ai_assistant_enabled = maybe_from_nullable(
            self.ai_assistant_enabled
        )
        self.assistant_tools_enabled = maybe_from_nullable(
            self.assistant_tools_enabled
        )
        self.prompt_engineering_step_enabled = maybe_from_nullable(
            self.prompt_engineering_step_enabled
        )
        self.first_day_of_week_from_locale = maybe_from_nullable(
            self.first_day_of_week_from_locale
        )
        self.inline_feedback_on_quizzes_enabled = maybe_from_nullable(
            self.inline_feedback_on_quizzes_enabled
        )
        self.quiz_single_question_mode_hide_run_button_enabled = (
            maybe_from_nullable(
                self.quiz_single_question_mode_hide_run_button_enabled
            )
        )
        self.warning_for_missing_newline_enabled = maybe_from_nullable(
            self.warning_for_missing_newline_enabled
        )
        self.jupyter_notebook_editor_enabled = maybe_from_nullable(
            self.jupyter_notebook_editor_enabled
        )
        self.jupyter_notebook_running_enabled = maybe_from_nullable(
            self.jupyter_notebook_running_enabled
        )
        self.coding_question_editor_reset_answer_enabled = maybe_from_nullable(
            self.coding_question_editor_reset_answer_enabled
        )
        self.coding_question_solution_enabled = maybe_from_nullable(
            self.coding_question_solution_enabled
        )
        self.download_editor_files_enabled = maybe_from_nullable(
            self.download_editor_files_enabled
        )
        self.quiz_view_modes_enabled = maybe_from_nullable(
            self.quiz_view_modes_enabled
        )
        self.regex_atv2_explanation_enabled = maybe_from_nullable(
            self.regex_atv2_explanation_enabled
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
        return res

    @classmethod
    def from_dict(
        cls: t.Type[FrontendSiteSettings], d: t.Dict[str, t.Any]
    ) -> FrontendSiteSettings:
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
        )
        res.raw_data = d
        return res
