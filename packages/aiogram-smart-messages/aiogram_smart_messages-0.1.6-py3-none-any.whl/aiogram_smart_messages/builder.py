# -*- coding: utf-8 -*-
"""
Keyboard builder module for Telegram bots.

This module provides utility classes for building Telegram keyboards
from JSON-based button descriptions, supporting both inline and reply keyboards.
"""

from typing import List, Dict, Any

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)


class KeyboardBuilder:
    """
    Utility class for building Telegram keyboards from JSON descriptions.
    
    This class provides static methods to construct inline keyboards and
    reply keyboards from structured data. It supports various button types
    including callback buttons, URL buttons, WebApp buttons, and inline
    query switches.
    
    All methods are static and can be called without instantiating the class.
    """

    @staticmethod
    def build_inline_keyboard(button_rows: List[List[Dict[str, Any]]]) -> InlineKeyboardMarkup:
        """
        Build an InlineKeyboardMarkup from button row descriptions.

        Creates a Telegram inline keyboard from a structured list of button
        definitions. Each button must have a 'type' field specifying the
        button behavior.

        Args:
            button_rows: List of button rows, where each row is a list of button
                        dictionaries. Each button dict should contain:
                        - type (str): Button type - 'callback', 'url', 'webapp',
                                     or 'switch_inline_query'
                        - text (str): Display text for the button
                        - data (str): Button-specific data (callback_data, URL, etc.)

        Returns:
            InlineKeyboardMarkup object ready to be attached to a message.

        Raises:
            KeyError: If required button fields ('text', 'data') are missing.

        Example:
            >>> buttons = [
            ...     [
            ...         {'type': 'callback', 'text': 'Option 1', 'data': 'opt1'},
            ...         {'type': 'callback', 'text': 'Option 2', 'data': 'opt2'}
            ...     ],
            ...     [
            ...         {'type': 'url', 'text': 'Visit Site', 'data': 'https://example.com'}
            ...     ]
            ... ]
            >>> keyboard = KeyboardBuilder.build_inline_keyboard(buttons)

        Note:
            Buttons without a 'type' field are silently skipped. Consider using
            strict validation if this behavior is not desired.
        """
        keyboard: List[List[InlineKeyboardButton]] = []
        
        for row in button_rows:
            buttons: List[InlineKeyboardButton] = []
            
            for button in row:
                if "type" not in button:
                    continue  # Skip buttons without type specification
                
                button_type = button["type"]
                button_text = button["text"]
                button_data = button["data"]
                
                if button_type == "callback":
                    buttons.append(
                        InlineKeyboardButton(
                            text=button_text,
                            callback_data=button_data
                        )
                    )
                elif button_type == "url":
                    buttons.append(
                        InlineKeyboardButton(
                            text=button_text,
                            url=button_data
                        )
                    )
                elif button_type == "webapp":
                    buttons.append(
                        InlineKeyboardButton(
                            text=button_text,
                            web_app=WebAppInfo(url=button_data)
                        )
                    )
                elif button_type == "switch_inline_query":
                    buttons.append(
                        InlineKeyboardButton(
                            text=button_text,
                            switch_inline_query=button_data
                        )
                    )
            
            if buttons:  # Only add non-empty rows
                keyboard.append(buttons)
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def build_reply_keyboard(
        button_rows: List[List[Dict[str, Any]]],
        resize_keyboard: bool = True,
        one_time_keyboard: bool = False,
        input_field_placeholder: str | None = None,
        selective: bool = False,
    ) -> ReplyKeyboardMarkup:
        """
        Build a ReplyKeyboardMarkup from button row descriptions.

        Creates a Telegram reply keyboard from a structured list of button
        definitions. Supports regular text buttons and WebApp buttons.

        Args:
            button_rows: List of button rows, where each row is a list of button
                        dictionaries. Each button dict should contain:
                        - text (str): Display text for the button
                        - type (str, optional): 'webapp' for WebApp buttons
                        - data (str, optional): WebApp URL if type is 'webapp'
            resize_keyboard: Request clients to resize the keyboard vertically
                           for optimal fit. Defaults to True.
            one_time_keyboard: Request clients to hide the keyboard after use.
                             Defaults to False.
            input_field_placeholder: Placeholder text shown in the input field
                                   when the keyboard is active.
            selective: Show the keyboard only to specific users mentioned in the
                     message or replying to the bot.

        Returns:
            ReplyKeyboardMarkup object ready to be attached to a message.

        Raises:
            KeyError: If required button field 'text' is missing.

        Example:
            >>> buttons = [
            ...     [
            ...         {'text': 'Main Menu'},
            ...         {'text': 'Settings'}
            ...     ],
            ...     [
            ...         {'type': 'webapp', 'text': 'Open App', 'data': 'https://app.example.com'}
            ...     ]
            ... ]
            >>> keyboard = KeyboardBuilder.build_reply_keyboard(
            ...     buttons,
            ...     one_time_keyboard=True,
            ...     input_field_placeholder="Choose an option..."
            ... )

        Note:
            Regular buttons (without 'type' field) will trigger a message with
            the button text when pressed. WebApp buttons will open the specified
            web application.
        """
        keyboard: List[List[KeyboardButton]] = []
        
        for row in button_rows:
            button_row: List[KeyboardButton] = []
            
            for button in row:
                button_text = button["text"]
                
                if button.get("type") == "webapp":
                    button_row.append(
                        KeyboardButton(
                            text=button_text,
                            web_app=WebAppInfo(url=button["data"])
                        )
                    )
                else:
                    button_row.append(KeyboardButton(text=button_text))
            
            if button_row:  # Only add non-empty rows
                keyboard.append(button_row)
        
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=one_time_keyboard,
            input_field_placeholder=input_field_placeholder,
            selective=selective,
        )