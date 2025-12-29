import time
import telegram
from .helpers import get_env_variable
from telegram.error import RetryAfter


class TelegramClient:
    def __init__(self, token=None, max_message_length=4096):
        self.token = token or get_env_variable("TELEGRAM_BOT_TOKEN")
        self.telegram = telegram.Bot(token=self.token)
        self.max_message_length = max_message_length

    def split_message(self, text: str):
        if len(text) <= self.max_message_length:
            return [text]

        messages = []
        while len(text) > self.max_message_length:
            cut_position = self.max_message_length
            for delimiter in ["\n\n", "\n", ". ", "! ", "? ", " "]:
                delimiter_position = text.rfind(delimiter, 0, self.max_message_length)
                if delimiter_position != -1:
                    cut_position = delimiter_position + len(delimiter)
                    break

            messages.append(text[:cut_position])
            text = text[cut_position:].lstrip()

        if text:
            messages.append(text)

        return messages

    async def send_message(
            self, chat_id, text, parse_mode=None, disable_notification=False,
            max_retries=5, timeout_delay=20
    ):
        parts = self.split_message(text)
        sent_messages = []

        for part in parts:
            retries = 0
            while retries < max_retries:
                try:
                    message = await self.telegram.send_message(
                        chat_id=chat_id,
                        text=part,
                        parse_mode=parse_mode,
                        disable_notification=disable_notification,
                        read_timeout=timeout_delay
                    )
                    sent_messages.append(message)
                    break
                except RetryAfter as e:
                    time.sleep(int(e.retry_after) + 1)
                retries += 1
            else:
                return None

            time.sleep(0.05)

        return sent_messages[-1] if sent_messages else None
