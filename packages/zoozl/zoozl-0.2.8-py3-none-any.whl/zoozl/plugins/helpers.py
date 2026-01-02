"""Example plugin to showcase zoozl chatbot mechanics."""

import random

from rapidfuzz import process

from zoozl.chatbot import Interface, Message


class Help(Interface):
    """Defines helper constructor for chat."""

    aliases = {"do get help", "help"}
    helps = (
        "I can't do much. I can only play a game.",
        "I can play games.",
        "You can try to play games.",
    )

    async def consume(self, package):
        """Try to help user."""
        package.callback(random.choice(self.helps))

    def is_complete(self):
        """Complete immediately the conversation."""
        return True


class Hello(Interface):
    """Defines hello commands."""

    aliases = {"hello", "hi", "how are you", "hey"}

    async def consume(self, package):
        """Greet the user."""
        greets = ["Hello", "Hey", "Hello, hello. What do you want to do?"]
        package.callback(random.choice(greets))

    def is_complete(self):
        """Complete immediately the conversation."""
        return True


def count_bulls_cows(challenge, number):
    """Count bulls and cows."""
    bulls = 0
    cows = 0
    for i, guess in enumerate(challenge):
        for j, value in enumerate(number):
            if guess == value:
                if i == j:
                    bulls += 1
                else:
                    cows += 1
                break
    return bulls, cows


class Games(Interface):
    """Defines games."""

    aliases = {"play games"}
    complete = False

    def is_complete(self):
        """Return if conversation is complete."""
        return self.complete

    async def consume(self, package):
        """Take latest text from user and process it."""
        if "game" not in package.conversation.data:
            self.get_game(package)
        else:
            getattr(self, package.conversation.data["game"])(package)

    def get_game(self, package):
        """Try to get game name or ask for it."""
        games = {
            "bull": "bull_game",
            "bulls and cows": "bull_game",
            "bulls & cows": "bull_game",
            "yes": "bull_game",
        }
        game = process.extractOne(
            package.conversation.messages[-1].text.lower(), games.keys()
        )
        if game[1] >= 95:
            package.conversation.data["game"] = games[game[0]]
            package.callback("OK. Let's play bulls and cows")
            self.bull_game(package)
        else:
            package.callback(Message("what game you want to play? bulls and cows?"))

    def bull_game(self, package):
        """Play a number guessing game."""
        if "bull_number" in package.conversation.data:
            number = package.last_message_text
            if len(number) != 4:
                package.callback(Message("Give number with exactly 4 digits"))
            elif len(set(number)) != len(number):
                package.callback("Digits must be unique in number")
            else:
                bulls, cows = count_bulls_cows(
                    number, package.conversation.data["bull_number"]
                )
                if bulls == 4:
                    package.callback("Congrats. You guessed right")
                    self.complete = True
                else:
                    package.callback(f"You have {bulls} bulls and {cows} cows")
        else:
            number = ""
            while len(number) < 4:
                digit = random.choice("0123456789")
                if len(number) == 0 and digit != "0":
                    number += digit
                    continue
                if digit in number:
                    continue
                number += digit
            package.conversation.data["bull_number"] = number
            package.callback("Guess 4 digit number")
