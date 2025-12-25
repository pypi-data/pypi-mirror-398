# -*- coding: utf-8 -*-
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)


class KeyboardBuilder:
    """
    Утилитный класс для сборки клавиатур из JSON-описания.
    Поддерживает inline-клавиатуры и обычные клавиатуры.
    """

    @staticmethod
    def build_inline_keyboard(button_rows: list[list[dict]]) -> InlineKeyboardMarkup:
        """
        Собирает InlineKeyboardMarkup из описания кнопок в JSON.
        """
        keyboard = []

        for row in button_rows:
            buttons = []
            for button in row:
                if "type" not in button:
                    continue  # или raise ValueError("Missing 'type' in inline button")
                if button["type"] == "callback":
                    buttons.append(
                        InlineKeyboardButton(
                            text=button["text"], callback_data=button["data"]
                        )
                    )
                elif button["type"] == "url":
                    buttons.append(
                        InlineKeyboardButton(text=button["text"], url=button["data"])
                    )
                elif button["type"] == "webapp":
                    buttons.append(
                        InlineKeyboardButton(
                            text=button["text"], web_app=WebAppInfo(url=button["data"])
                        )
                    )
                elif button["type"] == "switch_inline_query":
                    buttons.append(
                        InlineKeyboardButton(
                            text=button["text"], switch_inline_query=button["data"]
                        )
                    )
            keyboard.append(buttons)
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def build_reply_keyboard(button_rows: list[list[dict]]) -> ReplyKeyboardMarkup:
        """
        Собирает ReplyKeyboardMarkup из описания кнопок в JSON.
        Поддерживает обычные кнопки и WebApp-кнопки (если указан 'type': 'webapp').
        """
        keyboard = []

        for row in button_rows:
            button_row = []
            for button in row:
                if button.get("type") == "webapp":
                    button_row.append(
                        KeyboardButton(
                            text=button["text"], web_app=WebAppInfo(url=button["data"])
                        )
                    )
                else:
                    button_row.append(KeyboardButton(text=button["text"]))
            keyboard.append(button_row)

        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
