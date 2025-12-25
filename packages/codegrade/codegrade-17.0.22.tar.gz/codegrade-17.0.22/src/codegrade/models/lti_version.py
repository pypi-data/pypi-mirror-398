"""This module defines the enum LTIVersion.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from enum import Enum


class LTIVersion(str, Enum):
    v1_1 = "v1_1"
    v1_3 = "v1_3"
