# src/sherlock_ai/config/__init__.py
"""
Configuration classes for sherlock-ai package
"""

from .logging import LogFileConfig, LoggerConfig, LoggingConfig, LoggingPresets

SHERLOCK_AI_API_BASE_URL = "http://localhost:8000/v1/logs"
INJEST_LOGS_ENDPOINT = "injest-error-insights"
INJEST_PERFORMANCE_INSIGHTS_ENDPOINT = "injest-performance-insights"

__all__ = [
    "LogFileConfig",
    "LoggerConfig",
    "LoggingConfig",
    "LoggingPresets",
    "SHERLOCK_AI_API_BASE_URL",
    "INJEST_LOGS_ENDPOINT",
    "INJEST_PERFORMANCE_INSIGHTS_ENDPOINT",
]