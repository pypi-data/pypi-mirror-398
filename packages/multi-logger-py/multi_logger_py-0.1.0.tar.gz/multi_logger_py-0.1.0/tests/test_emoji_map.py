from package.emojis import Level


class TestEmojiMap:
    def test_level_to_emoji(self):
        """Test that each log level maps to the correct emoji."""
        expected_map = {
            Level.DEBUG: "🐛",
            Level.INFO: "ℹ️",
            Level.WARNING: "⚠️",
            Level.ERROR: "❌",
            Level.SUCCESS: "✅",
            Level.CRITICAL: "🔥",
        }
        for level, expected_emoji in expected_map.items():
            assert level.emoji == expected_emoji
