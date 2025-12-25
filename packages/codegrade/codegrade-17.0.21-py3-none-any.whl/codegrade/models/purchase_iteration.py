"""This module defines the enum PurchaseIteration.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

from enum import Enum


class PurchaseIteration(str, Enum):
    first = "first"
    second = "second"
