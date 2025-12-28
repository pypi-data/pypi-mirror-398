import telekit
import typing

import telebot.types


class StartHandler(telekit.Handler):

    # ------------------------------------------
    # Initialization
    # ------------------------------------------

    @classmethod
    def init_handler(cls, bot: telebot.TeleBot) -> None:
        """
        Initializes the command handler.
        """
        @cls.message_handler(commands=['start'])
        def handler(message: telebot.types.Message) -> None:
            cls(message).handle()

    # ------------------------------------------
    # Handling Logic
    # ------------------------------------------

    def handle(self) -> None:
        self.chain.sender.set_title("Hello!")
        self.chain.sender.set_message("Welcome here")

        self.chain.sender.set_photo("https://upload.wikimedia.org/wikipedia/commons/7/78/Image.jpg")

        self.chain.sender.set_effect(self.chain.sender.Effect.FIRE)

        self.chain.send()