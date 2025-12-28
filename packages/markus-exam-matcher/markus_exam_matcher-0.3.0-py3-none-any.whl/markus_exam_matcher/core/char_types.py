"""
MarkUs Exam Matcher: Character Types

Information
===============================
This module defines the types of characters that the MarkUs Exam
Matcher could encounter.
"""

from enum import Enum


class CharType(Enum):
    LETTER = 0
    DIGIT = 1
