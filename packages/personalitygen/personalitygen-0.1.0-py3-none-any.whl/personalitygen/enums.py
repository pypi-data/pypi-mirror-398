"""Enums for personalitygen."""

from __future__ import annotations

from enum import Enum


class LifeStage(str, Enum):
    CHILD = "child"
    YOUNG_ADULT = "young_adult"
    ADULT = "adult"


class PriorityLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
