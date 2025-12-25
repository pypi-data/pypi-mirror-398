"""This module defines the enum CoursePermission.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from enum import Enum


class CoursePermission(str, Enum):
    can_add_own_inline_comments = "can_add_own_inline_comments"
    can_always_use_all_upload_types = "can_always_use_all_upload_types"
    can_approve_inline_comments = "can_approve_inline_comments"
    can_archive_courses = "can_archive_courses"
    can_assign_graders = "can_assign_graders"
    can_create_assignment = "can_create_assignment"
    can_create_groups = "can_create_groups"
    can_create_test_submissions = "can_create_test_submissions"
    can_delete_assignments = "can_delete_assignments"
    can_delete_autotest_run = "can_delete_autotest_run"
    can_delete_submission = "can_delete_submission"
    can_edit_assignment_access_restrictions = (
        "can_edit_assignment_access_restrictions"
    )
    can_edit_assignment_info = "can_edit_assignment_info"
    can_edit_autotest = "can_edit_autotest"
    can_edit_cgignore = "can_edit_cgignore"
    can_edit_course_info = "can_edit_course_info"
    can_edit_course_roles = "can_edit_course_roles"
    can_edit_course_sections = "can_edit_course_sections"
    can_edit_course_users = "can_edit_course_users"
    can_edit_group_assignment = "can_edit_group_assignment"
    can_edit_group_set = "can_edit_group_set"
    can_edit_groups_after_submission = "can_edit_groups_after_submission"
    can_edit_maximum_grade = "can_edit_maximum_grade"
    can_edit_others_comments = "can_edit_others_comments"
    can_edit_others_groups = "can_edit_others_groups"
    can_edit_others_in_section_comments = "can_edit_others_in_section_comments"
    can_edit_others_in_section_groups = "can_edit_others_in_section_groups"
    can_edit_others_in_section_work = "can_edit_others_in_section_work"
    can_edit_others_work = "can_edit_others_work"
    can_edit_own_groups = "can_edit_own_groups"
    can_edit_pearson_context_templates = "can_edit_pearson_context_templates"
    can_edit_peer_feedback_settings = "can_edit_peer_feedback_settings"
    can_email_students = "can_email_students"
    can_grade_work = "can_grade_work"
    can_list_course_users = "can_list_course_users"
    can_manage_assignment_assistants = "can_manage_assignment_assistants"
    can_manage_course_snippets = "can_manage_course_snippets"
    can_manage_new_autotest = "can_manage_new_autotest"
    can_manage_plagiarism = "can_manage_plagiarism"
    can_override_submission_limiting = "can_override_submission_limiting"
    can_receive_login_links = "can_receive_login_links"
    can_run_autotest = "can_run_autotest"
    can_see_anonymized_names = "can_see_anonymized_names"
    can_see_archived_courses = "can_see_archived_courses"
    can_see_assignee = "can_see_assignee"
    can_see_assignments = "can_see_assignments"
    can_see_course_roles = "can_see_course_roles"
    can_see_grade_before_open = "can_see_grade_before_open"
    can_see_grade_history = "can_see_grade_history"
    can_see_hidden_assignments = "can_see_hidden_assignments"
    can_see_linter_feedback_before_done = "can_see_linter_feedback_before_done"
    can_see_others_in_section_work = "can_see_others_in_section_work"
    can_see_others_work = "can_see_others_work"
    can_see_peer_feedback_before_done = "can_see_peer_feedback_before_done"
    can_see_test_submissions = "can_see_test_submissions"
    can_see_user_feedback_before_done = "can_see_user_feedback_before_done"
    can_send_assistant_messages = "can_send_assistant_messages"
    can_send_assistant_messages_for_others = (
        "can_send_assistant_messages_for_others"
    )
    can_send_assistant_messages_for_others_in_section = (
        "can_send_assistant_messages_for_others_in_section"
    )
    can_submit_others_in_section_work = "can_submit_others_in_section_work"
    can_submit_others_work = "can_submit_others_work"
    can_submit_own_work = "can_submit_own_work"
    can_update_course_notifications = "can_update_course_notifications"
    can_update_grader_status = "can_update_grader_status"
    can_upload_after_deadline = "can_upload_after_deadline"
    can_upload_after_lock_date = "can_upload_after_lock_date"
    can_upload_bb_zip = "can_upload_bb_zip"
    can_upload_without_group = "can_upload_without_group"
    can_view_all_assignment_timeframes = "can_view_all_assignment_timeframes"
    can_view_analytics = "can_view_analytics"
    can_view_assistant_message_author = "can_view_assistant_message_author"
    can_view_assistant_system_prompt = "can_view_assistant_system_prompt"
    can_view_autotest_before_done = "can_view_autotest_before_done"
    can_view_autotest_fixture = "can_view_autotest_fixture"
    can_view_autotest_output_files_before_done = (
        "can_view_autotest_output_files_before_done"
    )
    can_view_autotest_step_details = "can_view_autotest_step_details"
    can_view_course_sections = "can_view_course_sections"
    can_view_course_snippets = "can_view_course_snippets"
    can_view_feedback_author = "can_view_feedback_author"
    can_view_hidden_autotest_steps = "can_view_hidden_autotest_steps"
    can_view_hidden_fixtures = "can_view_hidden_fixtures"
    can_view_inline_feedback_before_approved = (
        "can_view_inline_feedback_before_approved"
    )
    can_view_ip_restricted_assignments = "can_view_ip_restricted_assignments"
    can_view_new_autotest_hidden_step_configuration = (
        "can_view_new_autotest_hidden_step_configuration"
    )
    can_view_new_autotest_hidden_step_output = (
        "can_view_new_autotest_hidden_step_output"
    )
    can_view_new_autotest_hidden_step_results = (
        "can_view_new_autotest_hidden_step_results"
    )
    can_view_new_autotest_test_steps = "can_view_new_autotest_test_steps"
    can_view_others_comment_edits = "can_view_others_comment_edits"
    can_view_others_groups = "can_view_others_groups"
    can_view_others_in_section_comment_edits = (
        "can_view_others_in_section_comment_edits"
    )
    can_view_others_in_section_groups = "can_view_others_in_section_groups"
    can_view_own_course_section_members = "can_view_own_course_section_members"
    can_view_own_teacher_files = "can_view_own_teacher_files"
    can_view_password_restricted_assignments = (
        "can_view_password_restricted_assignments"
    )
    can_view_pearson_context_templates = "can_view_pearson_context_templates"
    can_view_peer_review_autotest_results = (
        "can_view_peer_review_autotest_results"
    )
    can_view_plagiarism = "can_view_plagiarism"
    manage_rubrics = "manage_rubrics"
