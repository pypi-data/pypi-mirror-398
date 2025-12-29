from httpx import post

BASE_URL = "https://api.telegram.org/bot{token}/{method}"


class TelegramClient:
    def __init__(
        self, token: Optional[str], chat_id: Optional[int], api_url: str = BASE_URL
    ):
        self._api_url = api_url
        self._token = token
        self._chat_id = chat_id

    def send_message(self, message: str) -> None:
        url = self._api_url.format(token=self._token, method="sendMessage")
        payload = {"chat_id": self._chat_id, "text": message}
        response = post(url, data=payload)
        response.raise_for_status()

    # TODO: implement async method
    def async_send_message(self, message: str) -> None:
        """Placeholder"""
        pass
