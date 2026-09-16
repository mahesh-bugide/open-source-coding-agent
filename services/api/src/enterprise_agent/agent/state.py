from __future__ import annotations

from enum import Enum


class AgentState(str, Enum):
    START = "START"
    UNDERSTAND = "UNDERSTAND"
    PLAN = "PLAN"
    SEARCH = "SEARCH"
    READ = "READ"
    EDIT = "EDIT"
    TEST = "TEST"
    ANALYZE_FAILURE = "ANALYZE_FAILURE"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
