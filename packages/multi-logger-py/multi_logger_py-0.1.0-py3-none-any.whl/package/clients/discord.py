from discord_webhook import AsyncDiscordWebhook, DiscordWebhook


class DiscordClient:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def send_message(self, message: str) -> None:
        """Send a message to the Discord channel.

        Args:
            message (str): The message to send.
        """
        webhook = DiscordWebhook(url=self.webhook_url, content=message)
        webhook.execute()

    async def send_message_async(self, message: str) -> None:
        """Send a message to the Discord channel asynchronously.

        Args:
            message (str): The message to send.
        """
        webhook = AsyncDiscordWebhook(url=self.webhook_url, content=message)
        await webhook.execute()
