"""
Emoji mappings for log levels.

This module provides emoji representations for different log levels
to enhance the visual appearance of log messages.
"""

from enum import Enum


### Emoji Level Enum tests: ./tests/test_emoji_map.py
class Level(str, Enum):
    """Emojis for different log levels.

    Attributes:
        DEBUG: Debug level emoji (🐛)
        INFO: Info level emoji (ℹ️)
        WARNING: Warning level emoji (⚠️)
        ERROR: Error level emoji (❌)
        SUCCESS: Success level emoji (✅)
        CRITICAL: Critical level emoji (🔥)
    """

    DEBUG = "🐛"
    INFO = "ℹ️"
    WARNING = "⚠️"
    ERROR = "❌"
    SUCCESS = "✅"
    CRITICAL = "🔥"

    @property
    def emoji(self) -> str:
        """Return the emoji string for this level (alias for value)."""
        return self.value

    @staticmethod
    def use_emoji(level_string: str) -> str:
        """Get the emoji representation of a log level.

        Args:
            level_string (str): Log level as a string (case-insensitive).

        Returns:
            str: Emoji corresponding to the log level, or the original
                string if no matching level is found.

        Example:
            >>> Level.use_emoji("debug")
            '🐛'
            >>> Level.use_emoji("INFO")
            'ℹ️'
            >>> Level.use_emoji("UNKNOWN")
            'UNKNOWN'
        """
        level_string = level_string.upper()
        if level_string in Level.__members__:
            return Level[level_string].value
        return level_string


__all__ = ["Level"]
