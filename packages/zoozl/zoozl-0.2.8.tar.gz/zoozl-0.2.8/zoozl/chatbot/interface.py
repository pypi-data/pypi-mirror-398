"""Main chat interface that external modules interact with.

>>> # callback is a function that accepts bot responses
>>> def callback(message):
        print(message.text)
>>> # root is the interface for chatbot to use to understand what to talk about
>>> root = chat.InterfaceRoot()
>>> root.load()
>>> # start unique conversation with a person
>>> bot = chat.Chat("unique_talker_id", callback, root)
>>> bot.greet()
>>> bot.ask(chat.Message("Hello"))
>>> root.close() # Important to call this, to close any resources opened
"""

import importlib
import logging

import membank

from zoozl import utils

from . import embeddings, api


log = logging.getLogger(__name__)


class InterfaceRoot:
    """Interface root for chatbot to use.

    Holds all possible commands and options chatbot can do.

    Must be always initialised before use:
    >>> root = InterfaceRoot(memory)
    >>> root.load()
    >>> root.close()

    Methods apart from load() are to be considered thread safe
    """

    def __init__(self, conf=None):
        """Configure with memory and configuration.

        :param conf: dictionary that holds all configuration for all Interfaces. If
            memory_path is not set, Root instance will hold memories of ongoing chats
            with talker only in the instance itself, closing instance will render all
            previous conversations forgotten. In such cases Root instance per talker
            should be kept alive as long as possible. if path is set, it must lead to
            valid path for Root instance to be able to store it's persistent memory,
            then history of talker conversations will be preserved upon instance
            destructions.
        """
        self._commands = {}
        self.conf = (
            conf
            if conf
            else {
                "extensions": ["zoozl.plugins.helpers"],
            }
        )
        self.lookup = None
        self.loaded = False
        self.memory = None

    def load(self):
        """Load interface map with available plugins and embedder."""
        self.memory = membank.LoadMemory(self.conf.get("memory_path", {}))
        if "embedder" in self.conf:
            self.lookup = embeddings.Lookup(self.memory, self.conf["embedder"])
        else:
            self.lookup = embeddings.Lookup(self.memory, embeddings.CharEmbedder())
        if "extensions" in self.conf:
            for interface in self.conf["extensions"]:
                extension = importlib.import_module(interface)
                for ext in utils.load_from_module(extension, api.Interface):
                    obj = ext()
                    obj.load(self)
                    for cmd in obj.aliases:
                        if cmd in self._commands:
                            raise RuntimeError(
                                f"Clash of interfaces! '{cmd}' already loaded"
                            )
                        self._commands[cmd] = obj
        # Load default command handlers, if not loaded by plugins
        if "cancel" not in self._commands:
            log.warning("No cancel command found in plugins.")
            self._commands["cancel"] = api.Interface()
        if "greet" not in self._commands:
            log.warning("No greet command found in plugins.")
            self._commands["greet"] = api.Interface()
        if "help" not in self._commands:
            log.warning("No help command found in plugins.")
            self._commands["help"] = api.Interface()
        self.loaded = True

    def close(self):
        """When membank supports close this should close it."""
        # self._m.close()

    async def consume(self, package, subject=None):
        """Route the package object to appropriate chat interface.

        :params package: a package object that contains data
        :params subject: optional subject, otherwise taken from package
        """
        subject = package.conversation.subject if subject is None else subject
        if subject not in self._commands:
            raise RuntimeError(f"There is no subject '{subject}' available.")
        await self._commands[subject].consume(package)

    def is_subject_complete(self, cmd):
        """Check if subject is complete."""
        return self._commands[cmd].is_complete()

    async def cancel(self, package):
        """Cancel the subject if needed."""
        await self.consume(package, "cancel")

    async def greet(self, package):
        """Greet the user, if any plugin has defined it."""
        await self.consume(package, "greet")

    def get_embedding(self, text):
        """Get embedding of the text."""
        return self.lookup.get(text)

    def get_interface_embeddings(self):
        """Return list of cmds and their embedding values."""
        if not self.loaded:
            raise RuntimeError("Interface map not loaded.")
        return [(cmd, self.get_embedding(cmd)) for cmd in self._commands]


def get_new_package(talker):
    """Return new Package object given talker.

    :params talker: unique identifier on talker for the conversation
    """
    return api.Conversation(talker=str(talker))


class Chat:
    """Interface for communication and routing with talker."""

    def __init__(self, talker, callback, interface_root):
        """Initialise comm interface with talker, one instance per talker.

        Talker must be something unique. This will serve as identification across
        several talkers that might turn to bot for chat.

        Callback must be a callable that accepts Message as only argument

        Interface_root is object that allows routing of messages to correct interfaces
        for the talker.
        """
        if not interface_root.loaded:
            raise RuntimeError("InterfaceRoot must be in loaded state!")
        self._root = interface_root
        self._callback = callback
        self._set_package(str(talker))

    def _set_package(self, talker):
        """Set package on the object."""
        conversation = self._root.memory.get.conversation(talker=talker, ongoing=True)
        if not conversation:
            conversation = api.Conversation(talker=talker)
        self._package = api.Package(conversation, self._call)

    def _save_package(self):
        """Save package to memory."""
        self._root.memory.put(self._package.conversation)

    async def greet(self):
        """Send first greeting message."""
        await self._root.greet(self._package)

    async def ask(self, message):
        """Make conversation by receiving text and sending message back to callback."""
        self.ongoing = True
        if self.subject:
            await self.do_subject(message)
        else:
            if not self.get_subject(message):
                self.set_subject("help")
            await self.do_subject(message)

    @property
    def talker(self):
        """Return talker."""
        return self._package.conversion.talker

    @property
    def ongoing(self):
        """Check if talk is ongoing."""
        return self._package.conversation.ongoing

    @ongoing.setter
    def ongoing(self, value):
        """Set talk ongoing value."""
        self._package.conversation.ongoing = value
        self._save_package()

    @property
    def subject(self):
        """Return subject if present."""
        return self._package.conversation.subject

    def get_subject(self, message):
        """Try to understand subject from message.

        if understood sets the subject and returns it otherwise returns None.
        """
        x = self._root.get_embedding(message.text)
        for cmd, e in self._root.get_interface_embeddings():
            eq = embeddings.get_cosine_similarity(x, e)
            if eq > 0.8:
                self.set_subject(cmd)
                return cmd
        return None

    def set_subject(self, cmd):
        """Set subject as per cmd."""
        self._package.conversation.subject = cmd
        self._save_package()

    def clear_subject(self):
        """Reset conversation to new start."""
        self._clean()

    async def do_subject(self, message):
        """Start or continue on the subject."""
        self._package.conversation.messages.append(message)
        if not await self._root.cancel(self._package):
            await self._root.consume(self._package)
            self._save_package()
        if self.subject and self._root.is_subject_complete(self.subject):
            self.clear_subject()

    def _call(self, message):
        """Construct Message and route it to callback.

        It must be either simple string text or Message object.
        """
        if not isinstance(message, api.Message):
            message = api.Message(message)
        message.author = self._root.conf.get("author", "")
        self._callback(message)

    def _clean(self):
        """Clean all data in conversation to initial state."""
        self._package.conversation.ongoing = False
        self._save_package()
        self._set_package(self._package.conversation.talker)
