# -*- coding: utf-8 -*-
"""
Smart message rendering module for Telegram bots.

This module provides functionality for loading, parsing, and sending "smart" messages
that can contain text, photos, and keyboards with support for localization and formatting.
"""

import os
from typing import Dict, List, Optional, Union, Any

from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
)

from ..message_engine import MessageEngine, SmartMessage
from ..builder import KeyboardBuilder
from ..loader import load_message_json
from ..decorators import with_error_logging
from ..logger import get_logger

logger = get_logger()


class SmartMessageRenderer:
    """
    A class for loading, parsing, and sending "smart" messages.
    
    Smart messages can contain text, photos, and buttons with full support
    for localization and context-based formatting.
    
    This class provides static and class methods for:
    - Loading message data from JSON files
    - Parsing JSON blocks into SmartMessage objects
    - Sending, editing, and replying with smart messages
    - Handling document uploads
    """

    @staticmethod
    @with_error_logging(logger=logger, error_label="LOAD_JSON", reraise=True)
    def load_json(
        namespace: Optional[str],
        role: str,
        lang: str,
        menu_file: str,
        block_key: str,
        context: Optional[Dict[str, Any]],
        module: str = "main_bot",
    ) -> Dict[str, Any]:
        """
        Load a JSON message file and extract a specific block with formatting.

        This method loads a JSON file containing message templates, extracts
        the specified block, and formats text/captions/button data using the
        provided context dictionary.

        Args:
            namespace: Optional namespace for organizing photos (NOT used in JSON path).
            role: User role for message selection (e.g., 'admin', 'user', 'common').
            lang: Language code for localization (e.g., 'ru', 'en').
            menu_file: Menu file name without extension (e.g., 'main_menu').
            block_key: Key path to the block in JSON. Supports nested keys with dots
                      (e.g., 'main.welcome' for nested structure).
            context: Dictionary with variables for string formatting. Can be None
                    if no formatting is needed.
            module: Module name for file path resolution. Defaults to 'main_bot'.

        Returns:
            Dictionary containing the message block data with all text fields
            formatted using the provided context.

        Raises:
            ValueError: If the specified block_key cannot be found in the JSON structure.

        Example:
            >>> renderer = SmartMessageRenderer()
            >>> block = renderer.load_json(
            ...     namespace=None,
            ...     role='admin',
            ...     lang='ru',
            ...     menu_file='notifications',
            ...     block_key='on_startup',
            ...     context={'username': 'John'}
            ... )
        """
        def deep_get(
            dictionary: Dict[str, Any],
            keys: str,
            default: Optional[Any] = None
        ) -> Any:
            """
            Retrieve a value from a nested dictionary using dot notation.

            Args:
                dictionary: The dictionary to search in.
                keys: Dot-separated key path (e.g., 'parent.child.value').
                default: Value to return if key path is not found.

            Returns:
                The value at the specified key path, or default if not found.
            """
            keys_list = keys.split(".")
            current = dictionary
            for key in keys_list:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            return current

        use_cache = not context
        # Path: module/messages/role/lang/menu_file.json
        # namespace is NOT used in the path - it's only for photo organization
        data = load_message_json(
            namespace or "", role, lang, f"{menu_file}.json", module, use_cache=use_cache
        )
        block = deep_get(data, block_key) if block_key else data

        if block is None:
            raise ValueError(
                f"SmartMessageRenderer.load_json could not find block_key '{block_key}' "
                f"in {menu_file}.json (role={role}, lang={lang}). "
                f"Check the JSON structure and key path."
            )

        if context:
            if "photo" in block:
                block["photo"] = block["photo"].format(**context)
            if "text" in block:
                block["text"] = block["text"].format(**context)
            if "caption" in block:
                block["caption"] = block["caption"].format(**context)
            if "buttons" in block:
                for row in block["buttons"]:
                    for button in row:
                        if "data" in button:
                            button["data"] = button["data"].format(**context)
                        if "text" in button:
                            button["text"] = button["text"].format(**context)
        return block

    @staticmethod
    @with_error_logging(logger=logger, error_label="PARSE_TO_SMART", reraise=True)
    def parse_to_smart(
        block: Dict[str, Any],
        namespace: Optional[str],
        role: str,
        lang: str,
        custom_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
        module: str = "main_bot",
        extra_kb: Optional[List[Dict[str, Any]]] = None,
        extra_kb_position: str = "bottom",
    ) -> SmartMessage:
        """
        Parse a message block dictionary into a SmartMessage object.

        This method transforms raw message data into a SmartMessage object,
        loading photos from filesystem or using Telegram file_ids, and building
        appropriate keyboards from button definitions.

        Args:
            block: Dictionary containing message data (text, photo, buttons, etc.).
            namespace: Optional namespace for organizing photos (used in photo path).
            role: User role for file path resolution.
            lang: Language code for file path resolution.
            custom_markup: Optional pre-built keyboard markup to override block buttons.
            module: Module name for file path resolution. Defaults to 'main_bot'.
            extra_kb: Additional keyboard buttons to add to the message. Can be a list
                     of button dicts or a list of rows of button dicts.
            extra_kb_position: Where to add extra_kb buttons - 'top' or 'bottom'.
                              Defaults to 'bottom'.

        Returns:
            SmartMessage object ready to be sent via MessageEngine.

        Raises:
            ValueError: If block is None or not a dictionary, indicating invalid
                       input data or missing block_key in JSON.

        Example:
            >>> block = {'text': 'Hello!', 'buttons': [[{'text': 'OK', 'data': 'ok'}]]}
            >>> msg = SmartMessageRenderer.parse_to_smart(
            ...     block=block,
            ...     namespace='start',
            ...     role='admin',
            ...     lang='ru'
            ... )
        """
        if block is None or not isinstance(block, dict):
            raise ValueError(
                f"SmartMessageRenderer.parse_to_smart received invalid block: {block!r}. "
                f"Most likely: block_key not found in JSON or JSON formatting error."
            )
        
        if extra_kb:
            # Normalize extra_kb to list[list[dict]] format
            if isinstance(extra_kb, list) and extra_kb and isinstance(extra_kb[0], dict):
                extra_kb = [extra_kb]

            # Merge extra_kb with existing buttons
            if "buttons" in block and isinstance(block["buttons"], list):
                if extra_kb_position == "top":
                    block["buttons"] = extra_kb + block["buttons"]
                else:
                    block["buttons"].extend(extra_kb)
            else:
                block["buttons"] = list(extra_kb)

        photo = block.get("photo")
        photo_file: Optional[Union[str, FSInputFile]] = None

        if photo:
            # Check if photo is a Telegram file_id (no slashes, backslashes, or dots)
            is_probably_file_id = isinstance(photo, str) and not any(
                c in photo for c in ["/", "\\", "."]
            )
            if is_probably_file_id:
                photo_file = photo
            else:
                # Photo path: module/namespace/photos/role/lang/photo_filename
                # If namespace is None, use empty string (photos directly in module/photos/)
                ns_part = f"{namespace}/" if namespace else ""
                photo_path = f"{module}/{ns_part}photos/{role}/{lang}/{photo}"
                if os.path.exists(photo_path):
                    photo_file = FSInputFile(photo_path)

        reply_markup = custom_markup
        if not reply_markup and "buttons" in block:
            if block.get("reply_keyboard", False):
                reply_markup = KeyboardBuilder.build_reply_keyboard(block["buttons"])
            else:
                reply_markup = KeyboardBuilder.build_inline_keyboard(block["buttons"])

        return SmartMessage(
            text=block.get("text"),
            caption=block.get("caption"),
            photo=photo_file,
            reply_markup=reply_markup,
        )

    @classmethod
    @with_error_logging(logger=logger, error_label="SEND_SMART_MESSAGE")
    async def send(
        cls,
        engine: MessageEngine,
        source: Union[Message, CallbackQuery, int],
        role: str = "user",
        module: str = "main_bot",
        namespace: Optional[str] = None,
        menu_file: Optional[str] = None,
        block_key: Optional[str] = None,
        lang: str = "ru",
        context: Optional[Dict[str, Any]] = None,
        custom_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
        override_block: Optional[Dict[str, Any]] = None,
        raise_errors: bool = False,
        extra_kb: Optional[List[Dict[str, Any]]] = None,
        extra_kb_position: str = "bottom",
    ) -> Optional[Message]:
        """
        Send a smart message to a chat.

        This method loads a message from JSON (or uses override_block), parses it
        into a SmartMessage, and sends it via the MessageEngine.

        Args:
            engine: MessageEngine instance for sending messages.
            source: Message or CallbackQuery to determine the chat and user.
            role: User role for message selection.
            module: Module name for file path resolution. Defaults to 'main_bot'.
            namespace: Optional namespace for organizing photos. Defaults to None.
            menu_file: Menu file name without extension. Required unless override_block is provided.
            block_key: Key path to the block in JSON. Required unless override_block is provided.
            lang: Language code for localization. Defaults to 'ru'.
            context: Dictionary with variables for string formatting.
            custom_markup: Optional pre-built keyboard markup to override block buttons.
            override_block: Dictionary with message data to use instead of loading from JSON.
            raise_errors: Whether to raise exceptions on send errors. Defaults to False.
            extra_kb: Additional keyboard buttons to add to the message.
            extra_kb_position: Where to add extra_kb buttons - 'top' or 'bottom'.

        Returns:
            Sent Message object, or None if sending failed and raise_errors is False.

        Raises:
            ValueError: If menu_file or block_key are missing when
                       override_block is not provided.

        Example:
            >>> await SmartMessageRenderer.send(
            ...     engine=message_engine,
            ...     source=message,
            ...     namespace='start',
            ...     menu_file='start',
            ...     block_key='greeting',
            ...     context={'username': 'Alice'}
            ... )
        """
        context = context or {}

        if override_block is not None:
            block = override_block
        else:
            if not menu_file or not block_key:
                logger.error(
                    f"Missing required parameters for SmartMessageRenderer.send: "
                    f"menu_file={menu_file}, block_key={block_key}"
                )
                raise ValueError(
                    "menu_file and block_key are required unless "
                    "override_block is provided."
                )
            
            block = cls.load_json(
                namespace, role, lang, menu_file, block_key, context, module=module
            )
        
        msg = cls.parse_to_smart(
            block, namespace, role, lang, custom_markup, module,
            extra_kb=extra_kb, extra_kb_position=extra_kb_position
        )

        return await engine.send_smart_message(
            source=source, msg=msg, raise_errors=raise_errors
        )

    @classmethod
    @with_error_logging(logger=logger, error_label="EDIT_SMART_MESSAGE")
    async def edit(
        cls,
        engine: MessageEngine,
        source: Union[Message, CallbackQuery],
        role: str = "user",
        module: str = "main_bot",
        namespace: Optional[str] = None,
        menu_file: Optional[str] = None,
        block_key: Optional[str] = None,
        lang: str = "ru",
        context: Optional[Dict[str, Any]] = None,
        custom_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
        override_block: Optional[Dict[str, Any]] = None,
        extra_kb: Optional[List[Dict[str, Any]]] = None,
        extra_kb_position: str = "bottom",
    ) -> Optional[Message]:
        """
        Edit an existing message with new content.

        This method loads a message from JSON (or uses override_block), parses it
        into a SmartMessage, and edits the existing message via the MessageEngine.

        Args:
            engine: MessageEngine instance for editing messages.
            source: Message or CallbackQuery containing the message to edit.
            role: User role for message selection.
            module: Module name for file path resolution. Defaults to 'main_bot'.
            namespace: Optional namespace for organizing photos. Defaults to None.
            menu_file: Menu file name without extension. Required unless override_block is provided.
            block_key: Key path to the block in JSON. Required unless override_block is provided.
            lang: Language code for localization. Defaults to 'ru'.
            context: Dictionary with variables for string formatting.
            custom_markup: Optional pre-built keyboard markup to override block buttons.
            override_block: Dictionary with message data to use instead of loading from JSON.
            extra_kb: Additional keyboard buttons to add to the message.
            extra_kb_position: Where to add extra_kb buttons - 'top' or 'bottom'.

        Returns:
            Edited Message object, or None if editing failed.

        Raises:
            ValueError: If menu_file or block_key are missing when override_block
                       is not provided.

        Example:
            >>> await SmartMessageRenderer.edit(
            ...     engine=message_engine,
            ...     source=callback_query,
            ...     namespace='settings',
            ...     menu_file='settings',
            ...     block_key='language_select',
            ... )
        """
        context = context or {}
        
        if override_block is not None:
            block = override_block
        else:
            if not menu_file or not block_key:
                logger.error(
                    f"Missing required parameters for SmartMessageRenderer.edit: "
                    f"menu_file={menu_file}, block_key={block_key}"
                )
                raise ValueError(
                    "menu_file and block_key are required unless "
                    "override_block is provided."
                )
            
            block = cls.load_json(
                namespace, role, lang, menu_file, block_key, context, module
            )
        
        msg = cls.parse_to_smart(
            block, namespace, role, lang, custom_markup, module,
            extra_kb=extra_kb, extra_kb_position=extra_kb_position
        )
        
        return await engine.edit_smart_message(source=source, msg=msg)

    @classmethod
    @with_error_logging(logger=logger, error_label="SMART_EDIT_OR_SEND")
    async def smart_edit_or_send(
        cls,
        engine: MessageEngine,
        source: Union[Message, CallbackQuery],
        role: str = "user",
        module: str = "main_bot",
        namespace: Optional[str] = None,
        menu_file: Optional[str] = None,
        block_key: Optional[str] = None,
        lang: str = "ru",
        context: Optional[Dict[str, Any]] = None,
        custom_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
        override_block: Optional[Dict[str, Any]] = None,
        extra_kb: Optional[List[Dict[str, Any]]] = None,
        extra_kb_position: str = "bottom",
    ) -> Optional[Message]:
        """
        Intelligently edit or re-send a message based on media content.

        This method determines whether to edit the existing message or delete it
        and send a new one. If the original message contains media (photo, video,
        or document), it will be deleted and a new message sent. Otherwise, it will
        be edited in place.

        Args:
            engine: MessageEngine instance for message operations.
            source: Message or CallbackQuery containing the message to update.
            role: User role for message selection.
            module: Module name for file path resolution. Defaults to 'main_bot'.
            namespace: Optional namespace for organizing photos. Defaults to None.
            menu_file: Menu file name without extension. Required unless override_block is provided.
            block_key: Key path to the block in JSON. Required unless override_block is provided.
            lang: Language code for localization. Defaults to 'ru'.
            context: Dictionary with variables for string formatting.
            custom_markup: Optional pre-built keyboard markup to override block buttons.
            override_block: Dictionary with message data to use instead of loading from JSON.
            extra_kb: Additional keyboard buttons to add to the message.
            extra_kb_position: Where to add extra_kb buttons - 'top' or 'bottom'.

        Returns:
            Updated or newly sent Message object, or None if operation failed.

        Raises:
            ValueError: If menu_file or block_key are missing when override_block
                       is not provided.

        Example:
            >>> await SmartMessageRenderer.smart_edit_or_send(
            ...     engine=message_engine,
            ...     source=callback_query,
            ...     namespace='catalog',
            ...     menu_file='catalog',
            ...     block_key='product_details',
            ...     context={'product_id': 123}
            ... )
        """
        context = context or {}
        
        if override_block is not None:
            block = override_block
        else:
            if not menu_file or not block_key:
                logger.error(
                    f"Missing required parameters for SmartMessageRenderer.smart_edit_or_send: "
                    f"menu_file={menu_file}, block_key={block_key}"
                )
                raise ValueError(
                    "menu_file and block_key are required unless "
                    "override_block is provided."
                )
            
            block = cls.load_json(
                namespace, role, lang, menu_file, block_key, context, module
            )

        msg = cls.parse_to_smart(
            block, namespace, role, lang, custom_markup, module,
            extra_kb=extra_kb, extra_kb_position=extra_kb_position
        )

        # Determine if original message has media
        original_msg = source.message if isinstance(source, CallbackQuery) else source
        has_media = bool(
            original_msg.photo or original_msg.video or original_msg.document
        )

        if has_media:
            await original_msg.delete()
            return await engine.send_smart_message(source=source, msg=msg)
        else:
            return await engine.edit_smart_message(source=source, msg=msg)

    @classmethod
    @with_error_logging(logger=logger, error_label="REPLY_SMART_MESSAGE")
    async def reply(
        cls,
        engine: MessageEngine,
        source: Message,
        role: str = "user",
        module: str = "main_bot",
        namespace: Optional[str] = None,
        menu_file: Optional[str] = None,
        block_key: Optional[str] = None,
        lang: str = "ru",
        context: Optional[Dict[str, Any]] = None,
        custom_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
        override_block: Optional[Dict[str, Any]] = None,
        raise_errors: bool = False,
        extra_kb: Optional[List[Dict[str, Any]]] = None,
        extra_kb_position: str = "bottom",
    ) -> Optional[Message]:
        """
        Send a smart message as a reply to another message.

        This method loads a message from JSON (or uses override_block), parses it
        into a SmartMessage, and sends it as a reply to the source message.

        Args:
            engine: MessageEngine instance for sending messages.
            source: Message to reply to.
            role: User role for message selection.
            module: Module name for file path resolution. Defaults to 'main_bot'.
            namespace: Optional namespace for organizing photos. Defaults to None.
            menu_file: Menu file name without extension. Required unless override_block is provided.
            block_key: Key path to the block in JSON. Required unless override_block is provided.
            lang: Language code for localization. Defaults to 'ru'.
            context: Dictionary with variables for string formatting.
            custom_markup: Optional pre-built keyboard markup to override block buttons.
            override_block: Dictionary with message data to use instead of loading from JSON.
            raise_errors: Whether to raise exceptions on send errors. Defaults to False.
            extra_kb: Additional keyboard buttons to add to the message.
            extra_kb_position: Where to add extra_kb buttons - 'top' or 'bottom'.

        Returns:
            Sent reply Message object, or None if sending failed and raise_errors is False.

        Raises:
            ValueError: If menu_file or block_key are missing when
                       override_block is not provided.

        Example:
            >>> await SmartMessageRenderer.reply(
            ...     engine=message_engine,
            ...     source=user_message,
            ...     namespace='responses',
            ...     menu_file='responses',
            ...     block_key='command_help',
            ... )
        """
        context = context or {}

        if override_block is not None:
            block = override_block
        else:
            if not menu_file or not block_key:
                logger.error(
                    f"Missing required parameters for SmartMessageRenderer.reply: "
                    f"menu_file={menu_file}, block_key={block_key}"
                )
                raise ValueError(
                    "menu_file and block_key are required unless "
                    "override_block is provided."
                )
            
            block = cls.load_json(
                namespace, role, lang, menu_file, block_key, context, module=module
            )

        msg = cls.parse_to_smart(
            block, namespace, role, lang, custom_markup, module,
            extra_kb=extra_kb, extra_kb_position=extra_kb_position
        )

        # Use engine's reply method if available, otherwise fallback to message.reply()
        if hasattr(engine, "reply_smart_message"):
            return await engine.reply_smart_message(
                source=source, msg=msg, raise_errors=raise_errors
            )
        else:
            # Fallback to standard reply
            return await source.reply(
                msg.text or msg.caption or "",
                reply_markup=msg.reply_markup,
                disable_web_page_preview=True,
            )

    @classmethod
    @with_error_logging(logger=logger, error_label="SEND_DOCUMENT")
    async def send_document(
        cls,
        engine: MessageEngine,
        source: Union[Message, int],
        document: FSInputFile,
        caption: str = "",
        custom_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
    ) -> Optional[Message]:
        """
        Send a document to a chat.

        This method sends a document file to the specified chat using the MessageEngine.

        Args:
            engine: MessageEngine instance for sending documents.
            source: Message object or chat_id (int) to send the document to.
            document: FSInputFile object containing the document to send.
            caption: Optional caption text for the document. Defaults to empty string.
            custom_markup: Optional keyboard markup to attach to the document message.

        Returns:
            Sent Message object containing the document, or None if sending failed.

        Example:
            >>> from aiogram.types import FSInputFile
            >>> doc = FSInputFile("report.pdf")
            >>> await SmartMessageRenderer.send_document(
            ...     engine=message_engine,
            ...     source=message.chat.id,
            ...     document=doc,
            ...     caption="Monthly Report"
            ... )
        """
        return await engine.send_document(
            source=source,
            document=document,
            caption=caption,
            custom_markup=custom_markup,
        )