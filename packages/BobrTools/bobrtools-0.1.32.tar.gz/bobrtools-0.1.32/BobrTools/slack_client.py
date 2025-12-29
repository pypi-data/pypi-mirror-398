from slack_sdk import WebClient
from .helpers import get_env_variable


class SlackClient():
    def __init__(self, token=None):
        self.token = token or get_env_variable("SLACK_BOT_TOKEN")
        self.slack = WebClient(token=self.token)

    def send_message(self, channel, text, thread_ts=None, parse=None):
        return self.slack.chat_postMessage(
            channel=channel,
            text=text,
            thread_ts=thread_ts,
            parse=parse
        )

    def __getattr__(self, name):
        """
        Fallback attribute resolver.

        If a method or attribute is not found in SlackClient,
        it will be retrieved from the internal Slack WebClient instance.
        This allows transparent access to all Slack API methods.

        :param name: Attribute or method name
        :return: Corresponding attribute/method from WebClient
        """
        return getattr(self.slack, name)
