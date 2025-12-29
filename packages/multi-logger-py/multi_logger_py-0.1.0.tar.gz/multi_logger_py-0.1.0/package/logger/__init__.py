from typing import Optional

from loguru import logger as loguru_logger

from package.clients.discord import DiscordClient
from package.clients.telegram import TelegramClient
from package.emojis import Level


class MultiLogger:
    def __init__(
        self,
        discord_webhook_url: Optional[str] = None,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[int] = None,
        use_emojis: bool = False,
    ) -> None:
        """Initialize MultiLogger with optional Discord and Telegram clients.

        Args:
            discord_webhook_url (str, optional): Discord webhook URL. Defaults to None.
            telegram_token (str, optional): Telegram bot token. Defaults to None.
            telegram_chat_id (int, optional): Telegram chat ID. Defaults to None.
            use_emojis (bool, optional): Whether to use emojis in log messages. Defaults to False.
        """
        self._discord_client = (
            DiscordClient(discord_webhook_url) if discord_webhook_url else None
        )
        self._telegram_client = (
            TelegramClient(telegram_token, telegram_chat_id)
            if telegram_token and telegram_chat_id
            else None
        )
        self.logger: None | loguru_logger = None
        self.use_emojis = use_emojis

    def _log(self, log_level: str, message: str):
        level = log_level.upper()

        if self.logger:
            log_method = getattr(self.logger, level.lower(), None)
            if log_method:
                log_method(message)

        if self.use_emojis:
            level = Level.use_emoji(level)
        msg = f"[{level}] {message}"

        if self._telegram_client:
            self._telegram_client.send_message(msg)

        if self._discord_client:
            self._discord_client.send_message(msg)

    def setup_logger(self, logger: loguru_logger | None) -> None:
        """
        Setup Loguru logger instance.

        Args:
            logger (loguru_logger): Loguru logger instance
        """
        if logger is None:
            self.logger = loguru_logger
            return

        self.logger = logger

    ### levels

    def debug(self, message: str) -> None:
        self._log("DEBUG", message)

    def info(self, message: str) -> None:
        self._log("INFO", message)

    def warning(self, message: str) -> None:
        self._log("WARNING", message)

    def error(self, message: str) -> None:
        self._log("ERROR", message)

    def success(self, message: str) -> None:
        self._log("SUCCESS", message)

    def critical(self, message: str) -> None:
        self._log("CRITICAL", message)
