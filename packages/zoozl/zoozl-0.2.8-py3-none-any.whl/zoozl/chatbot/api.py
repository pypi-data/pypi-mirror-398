"""API for extending chat interface.

Extension module should contain as a minimum one subclass of Interface
"""

from abc import abstractmethod
import base64
import datetime
import dataclasses
from dataclasses import dataclass
import uuid


def encode_array(lst):
    """Encode array of dataclasses."""
    return [encode_class(i) for i in lst]


def encode_class(cls):
    """Encode dataclass."""
    result = {}
    for i in dataclasses.fields(cls):
        if i.metadata.get("encode"):
            result[i.name] = i.metadata["encode"](getattr(cls, i.name))
        else:
            result[i.name] = getattr(cls, i.name)
    return result


@dataclass
class MessagePart:
    """Contains one single atomic communication piece between talker and bot.

    A Message will contain one or more MessageParts.
    """

    text: str = ""
    binary: bytes = dataclasses.field(
        default=b"", metadata={"encode": lambda x: base64.b64encode(x).decode()}
    )
    media_type: str = ""  # e.g text/plain, image/jpeg, application/json
    filename: str = ""
    consumed: bool = False

    def __post_init__(self):
        """Decode binary data."""
        if isinstance(self.binary, str):
            self.binary = base64.b64decode(self.binary)
        if not isinstance(self.text, str):
            raise ValueError(f"`{self.text}` must be a string.")
        if not isinstance(self.binary, bytes):
            raise ValueError("Binary must be bytes.")
        if not isinstance(self.media_type, str):
            raise ValueError(f"`{self.media_type}` must be a string.")
        if not isinstance(self.filename, str):
            raise ValueError(f"`{self.filename}` must be a string.")


@dataclass
class Message:
    """Message object to be exchanged between talker and bot.

    author - the talker who sent the message (e.g. user, bot)
    parts - list of MessagePart objects
    """

    parts: list = dataclasses.field(
        default_factory=list,
        metadata={"encode": encode_array},
    )
    author: str = ""
    sent: datetime = dataclasses.field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        metadata={"encode": lambda x: x.isoformat()},
    )

    def __post_init__(self):
        """Upload parts as MessageParts."""
        if isinstance(self.parts, str):
            self.parts = [MessagePart(self.parts)]
        else:
            self.parts = [
                MessagePart(**i) if isinstance(i, dict) else i for i in self.parts
            ]
        if isinstance(self.sent, str):
            self.sent = datetime.datetime.fromisoformat(self.sent)

    @property
    def text(self):
        """Return text part of the message."""
        return " ".join([part.text for part in self.parts])

    @property
    def files(self):
        """Return files."""
        return [(part.binary, part.media_type) for part in self.parts if part.binary]


@dataclass
class Conversation:
    """Conversation with people(talkers) who request actions.

    There can be many conversations for one talker, but preferably only one ongoing per
    talker at a time.
    """

    uuid: str = dataclasses.field(default="", metadata={"key": True})
    talker: str = ""
    ongoing: bool = False
    subject: str = ""
    messages: list = dataclasses.field(
        default_factory=list, metadata={"encode": encode_array}
    )
    data: dict = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        """Generate uuid automatically if not provided."""
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        if self.messages and isinstance(self.messages[0], dict):
            self.messages = [Message(**i) for i in self.messages]


@dataclass
class Package:
    """Package contains information data that is exchanged between bot and commands.

    conversation - saveable state of conversation between user and chatbot
    callback - a function to allow sending back Message object to user
        (as a convenience it is possible to send just text string that will be
        formatted into Message object automatically by interface)
    """

    conversation: Conversation
    callback: type

    @property
    def last_message(self):
        """Retrieve latest message from conversation."""
        if self.conversation.messages:
            return self.conversation.messages[-1]

    @property
    def last_message_text(self):
        """Retrieve latest text from conversation."""
        if self.conversation.messages:
            last_message = self.conversation.messages[-1]
            return last_message.text
        return ""

    @property
    def talker(self):
        """Return talker."""
        return self.conversation.talker

    def get_attachments(self, msg_count=1, consumed=None):
        """Return attachments from last N messages."""
        attachments = []
        for message in self.conversation.messages[-msg_count:]:
            for part in message.parts:
                if part.binary:
                    if consumed is None or part.consumed == consumed:
                        attachments.append(part)
        return attachments


class Interface:
    """Interface to the chat command handling.

    Subclass this to extend a chat module

    aliases - define a set of command functions that would trigger this event
    """

    # Command names as typed by the one who asks
    aliases = set()

    def load(self, root):
        """Preload once an Interface.

        :params root: interface root object
        """

    @abstractmethod
    async def consume(self, package):
        """Handle all requests when subject is triggered.

        :param context: InterfaceMap object that allows to communicate with other
            interfaces available apart from other things
        :param package: is a special object defined as Package, exchanges data
        """

    def is_complete(self):
        """Must return True or False."""
        return False
