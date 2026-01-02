"""Example plugin that sends always greeting message."""

from zoozl.chatbot import Interface


class Greet(Interface):
    """First greet message to the user."""

    aliases = {"greet"}

    async def consume(self, package):
        """Greet the user."""
        if package.conversation.ongoing:
            package.callback("Hey. What would you like me to do?")
        else:
            package.callback("Hello!")
            msg = "I can do few things. Ask me for example "
            msg += "to play games or something."
            package.callback(msg)
            package.conversation.ongoing = True
