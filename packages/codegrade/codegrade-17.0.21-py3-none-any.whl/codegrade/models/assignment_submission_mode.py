"""This module defines the enum AssignmentSubmissionMode.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from enum import Enum


class AssignmentSubmissionMode(str, Enum):
    full = "full"
    simple = "simple"
