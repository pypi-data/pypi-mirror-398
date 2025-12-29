"""
OmniCoreAgent Package

This package provides the high-level OmniCoreAgent interface and background agent functionality.
"""

from .agent import OmniCoreAgent
from .background_agent import (
    BackgroundOmniCoreAgent,
    BackgroundAgentManager,
    TaskRegistry,
    APSchedulerBackend,
    BackgroundTaskScheduler,
)

__all__ = [
    "OmniCoreAgent",
    "BackgroundOmniCoreAgent",
    "BackgroundAgentManager",
    "TaskRegistry",
    "APSchedulerBackend",
    "BackgroundTaskScheduler",
]
