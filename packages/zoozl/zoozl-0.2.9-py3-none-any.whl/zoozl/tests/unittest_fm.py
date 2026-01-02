"""Unittest framework test classes and functions."""

import email.message
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from zoozl import chatbot, emailer


class TestChatbot:
    """Object that supports testing directly with chatbot.

    >>> bot = TestChatbot()
    >>> bot.load()
    >>> bot.ask()
    >>> bot.close()
    """

    def __init__(self):
        """Load object with callback and memory mocks."""
        self._callback = MagicMock()
        self._memory = MagicMock()
        self._interfaces = None
        self.bot = None

    def load(self, conf=None, callback=None):
        """Load test chatbot with optional configuration."""
        callback = callback if callback is not None else self._callback
        self._interfaces = chatbot.InterfaceRoot(conf)
        self._interfaces.load()
        self.bot = chatbot.Chat("caller", callback, self._interfaces)

    def close(self):
        """Close interface."""
        self._interfaces.close()

    def last_text(self):
        """Return last received text message from callback."""
        return "\n".join(i.text for i in self.last_message().parts)

    def last_message(self):
        """Return last received message from callback."""
        try:
            self._callback.assert_called()
        except AssertionError:
            raise AssertionError("Bot did not make any responses.") from None
        return self._callback.call_args.args[0]

    async def ask(self, *args, **kwargs):
        """Ask bot."""
        await self.bot.ask(chatbot.Message(*args, **kwargs))

    async def greet(self):
        """Receive greeting from bot."""
        await self.bot.greet()

    def total_messages_sent(self):
        """Return number of messages sent back to callback so far."""
        return self._callback.call_count


class TestEmailbot(TestChatbot):
    """Object that supports testing directly with chatbot through email.

    >>> bot = TestEmailbot()
    >>> bot.load()
    >>> bot.ask()
    >>> bot.close()

    Object is not thread safe.
    """

    def __init__(self):
        """Initialise variables."""
        super().__init__()
        self._sender = None
        self._receiver = None
        self._subject = None
        self.received_emails = []

    def load(self, conf=None):
        """Load email chatbot compliant interface."""
        super().load(conf, self.callback)

    def callback(self, msg: chatbot.Message):
        """Simulate email message sending."""
        mail = emailer.deserialise_email(
            self._sender, self._receiver, self._subject, msg
        )
        self._callback(mail)

    async def ask(self, msg: email.message.Message):
        """Ask bot."""
        self._subject = msg["subject"]
        self._sender = msg["from"]
        self._receiver = msg["to"]
        return await self.bot.ask(emailer.serialise_email(msg))

    def last_text(self):
        """Return last received text message from callback."""
        return next(
            i.get_payload(decode=True).decode()
            for i in self.last_message().walk()
            if i.get_content_maintype() == "text"
        )


class ChatbotUnittest(IsolatedAsyncioTestCase):
    """Unittest testcase that supports TestChatbot assert methods."""

    def setUp(self):
        """Initialise chatbot."""
        self.bot = TestChatbot()
        self.bot.load()

    def tearDown(self):
        """Close interface."""
        self.bot.close()

    def assert_response(self, *args, **kwargs):
        """Assert bot has responded."""
        expected = chatbot.Message(*args, **kwargs)
        received = self.bot.last_message()
        self.assertEqual(expected.author, received.author)
        self.assertEqual(expected.sent.year, received.sent.year)
        self.assertEqual(expected.sent.month, received.sent.month)
        self.assertEqual(expected.sent.day, received.sent.day)
        for i, val in enumerate(expected.parts):
            self.assertEqual(val, received.parts[i])
        return received

    def assert_response_with_any(self, *messages):
        """Assert bot has responded with any of provided messages."""
        not_found = 0
        received = self.bot.last_message()
        for m in messages:
            try:
                self.assert_response(m)
            except AssertionError:
                not_found += 1
        # We expect not_found messages to be exactly 1 less than expected
        if not_found + 1 != len(messages):
            self.fail(
                f"None of {messages} were found in response {received}",
            )
