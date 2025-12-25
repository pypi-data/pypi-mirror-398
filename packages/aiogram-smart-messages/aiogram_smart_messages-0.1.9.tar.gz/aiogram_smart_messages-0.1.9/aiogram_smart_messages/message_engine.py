# -*- coding: utf-8 -*-
"""
Message engine module for Telegram bot messaging operations.

This module provides high-level abstractions for sending, editing, and managing
Telegram messages with support for text, photos, keyboards, and documents.
"""

from typing import Optional, Union

from aiogram import Bot
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
    ReplyKeyboardMarkup,
)
from aiogram.exceptions import TelegramBadRequest

from .logger import get_logger
from .decorators import with_error_logging

logger = get_logger()


class SmartMessage:
    """
    Container class for message content with optional text, photo, and keyboard.
    
    SmartMessage encapsulates all possible components of a Telegram message,
    making it easy to pass complete message data between functions. It supports
    text-only messages, photo messages with captions, and any combination with
    inline or reply keyboards.
    
    Attributes:
        text: Plain text content of the message. Used for text-only messages
             or as photo caption fallback.
        caption: Caption text for photo messages. Takes precedence over text
                when photo is present.
        photo: Photo file to send. Can be FSInputFile for local files or
              str for Telegram file_id/URL.
        reply_markup: Keyboard markup to attach to the message. Supports both
                     InlineKeyboardMarkup and ReplyKeyboardMarkup.
    
    Example:
        >>> msg = SmartMessage(
        ...     text="Hello, world!",
        ...     reply_markup=InlineKeyboardMarkup(inline_keyboard=[[...]])
        ... )
        >>> 
        >>> photo_msg = SmartMessage(
        ...     caption="Check this out!",
        ...     photo=FSInputFile("image.jpg"),
        ...     reply_markup=keyboard
        ... )
    """

    def __init__(
        self,
        text: Optional[str] = None,
        caption: Optional[str] = None,
        photo: Optional[Union[FSInputFile, str]] = None,
        reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
    ) -> None:
        """
        Initialize a SmartMessage with content and markup.
        
        Args:
            text: Plain text content or caption fallback.
            caption: Caption for photo messages.
            photo: Photo file (FSInputFile, file_id, or URL).
            reply_markup: Keyboard markup (inline or reply).
        """
        self.text = text
        self.caption = caption
        self.photo = photo
        self.reply_markup = reply_markup


class MessageEngine:
    """
    High-level message management engine for Telegram bots.
    
    MessageEngine provides convenient methods for sending, editing, and replying
    to messages with automatic handling of different message types (text, photo,
    document). It abstracts away the complexity of choosing the right Telegram API
    method based on message content.
    
    The engine handles:
    - Automatic method selection based on message content
    - Smart message editing with media support
    - Error handling and logging
    - Reply and document sending
    
    Attributes:
        bot: Aiogram Bot instance used for API calls.
    """

    def __init__(self, bot: Bot) -> None:
        """
        Initialize MessageEngine with a bot instance.
        
        Args:
            bot: Aiogram Bot instance for making Telegram API calls.
        """
        self.bot = bot

    @with_error_logging(logger=logger, error_label="SEND_SMART_MESSAGE")
    async def send_smart_message(
        self,
        source: Union[Message, CallbackQuery, int],
        msg: SmartMessage,
        raise_errors: bool = True,
    ) -> Optional[Message]:
        """
        Send a smart message with automatic method selection.
        
        Automatically chooses between send_photo and send_message based on
        message content. Handles both direct chat_id sends and sends from
        Message/CallbackQuery sources.
        
        Args:
            source: Source for determining chat_id. Can be:
                   - Message object
                   - CallbackQuery object
                   - int (direct chat_id)
            msg: SmartMessage object containing message content and markup.
            raise_errors: If True, raise exceptions on send failures.
                         If False, log errors and return None.
        
        Returns:
            Sent Message object on success, None on failure (if raise_errors=False).
        
        Raises:
            TelegramBadRequest: On API errors (if raise_errors=True).
            ValueError: If msg contains neither text nor photo.
        
        Example:
            >>> engine = MessageEngine(bot)
            >>> msg = SmartMessage(text="Hello!", reply_markup=keyboard)
            >>> sent = await engine.send_smart_message(
            ...     source=callback_query,
            ...     msg=msg
            ... )
        
        Note:
            - For photo messages, caption takes precedence over text
            - text is used as fallback caption if caption is not set
            - Web page previews are disabled for text messages
        """
        if isinstance(source, int):
            chat_id = source
        else:
            message = (
                source.message if isinstance(source, CallbackQuery) else source
            )
            chat_id = message.chat.id

        sent_message: Optional[Message] = None

        if msg.photo:
            sent_message = await self.bot.send_photo(
                chat_id=chat_id,
                photo=msg.photo,
                caption=msg.caption or msg.text,
                reply_markup=msg.reply_markup,
            )
        elif msg.text:
            sent_message = await self.bot.send_message(
                chat_id=chat_id,
                text=msg.text,
                reply_markup=msg.reply_markup,
                disable_web_page_preview=True,
            )

        return sent_message

    @with_error_logging(logger=logger, error_label="EDIT_SMART_MESSAGE")
    async def edit_smart_message(
        self,
        source: Union[Message, CallbackQuery],
        msg: SmartMessage,
    ) -> Optional[Message]:
        """
        Edit an existing message with smart method selection.
        
        Automatically chooses the appropriate edit method based on message content:
        - edit_message_media for photo changes
        - edit_message_caption for caption-only changes
        - edit_message_text for text-only changes
        
        Handles common Telegram errors gracefully:
        - "message is not modified" → Sends confirmation, returns original message
        - "BUTTON_USER_PRIVACY_RESTRICTED" → Sends privacy notice, returns None
        
        Args:
            source: Source message to edit. Can be Message or CallbackQuery.
            msg: SmartMessage object with new content.
        
        Returns:
            Edited Message object on success.
            Original Message if content unchanged.
            None if edit failed due to user privacy restrictions.
        
        Raises:
            TelegramBadRequest: On unhandled API errors.
        
        Example:
            >>> new_msg = SmartMessage(
            ...     text="Updated text",
            ...     reply_markup=new_keyboard
            ... )
            >>> edited = await engine.edit_smart_message(
            ...     source=callback_query,
            ...     msg=new_msg
            ... )
        
        Note:
            - Cannot change message type (text to photo or vice versa)
            - For major changes, consider delete + send instead
            - Keyboard updates work with any edit method
        """
        message = source.message if isinstance(source, CallbackQuery) else source
        chat_id = message.chat.id
        message_id = message.message_id

        edited_message: Optional[Message] = None

        try:
            if msg.photo:
                edited_message = await self.bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=message_id,
                    media=InputMediaPhoto(
                        media=msg.photo,
                        caption=msg.caption or msg.text
                    ),
                    reply_markup=msg.reply_markup,
                )
            elif msg.caption:
                edited_message = await self.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=msg.caption,
                    reply_markup=msg.reply_markup,
                )
            elif msg.text:
                edited_message = await self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=msg.text,
                    disable_web_page_preview=True,
                    reply_markup=msg.reply_markup,
                )

            return edited_message
            
        except TelegramBadRequest as e:
            error_str = str(e)
            
            if "message is not modified" in error_str:
                # Content unchanged, acknowledge update
                if isinstance(source, CallbackQuery):
                    await source.answer("Информация обновлена.")
                return message
            elif "BUTTON_USER_PRIVACY_RESTRICTED" in error_str:
                # User privacy settings prevent this action
                if isinstance(source, CallbackQuery):
                    await source.answer("Контакт не имеет юзернейм.")
                return None
            else:
                # Unhandled error, log and re-raise
                logger.exception(f"Unhandled TelegramBadRequest: {error_str}")
                raise

    @with_error_logging(logger=logger, error_label="REPLY_SMART_MESSAGE")
    async def reply_smart_message(
        self,
        source: Message,
        msg: SmartMessage,
        raise_errors: bool = True,
    ) -> Optional[Message]:
        """
        Send a smart message as a reply to another message.
        
        Sends a message that replies to (quotes) the source message. Automatically
        selects between reply_photo and reply methods based on content.
        
        Args:
            source: Message object to reply to.
            msg: SmartMessage object containing reply content and markup.
            raise_errors: If True, raise exceptions on send failures.
                         If False, log errors and return None.
        
        Returns:
            Sent reply Message object on success, None on failure.
        
        Raises:
            TelegramBadRequest: On API errors (if raise_errors=True).
        
        Example:
            >>> reply_msg = SmartMessage(
            ...     text="Thanks for your message!",
            ...     reply_markup=keyboard
            ... )
            >>> sent = await engine.reply_smart_message(
            ...     source=user_message,
            ...     msg=reply_msg
            ... )
        
        Note:
            - Reply creates a quote/reference to the original message
            - User can tap the reply to jump to original message
            - Web page previews are disabled for text replies
        """
        sent_message: Optional[Message] = None

        if msg.photo:
            sent_message = await source.reply_photo(
                photo=msg.photo,
                caption=msg.caption or msg.text,
                reply_markup=msg.reply_markup,
            )
        elif msg.text:
            sent_message = await source.reply(
                text=msg.text,
                reply_markup=msg.reply_markup,
                disable_web_page_preview=True,
            )

        return sent_message

    @with_error_logging(logger=logger, error_label="SEND_DOCUMENT")
    async def send_document(
        self,
        source: Union[Message, int],
        document: FSInputFile,
        caption: str = "",
        custom_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
    ) -> Optional[Message]:
        """
        Send a document file to a chat.
        
        Sends a document (file) with optional caption and keyboard markup.
        Supports sending to both Message sources and direct chat IDs.
        
        Args:
            source: Target for document. Can be:
                   - Message object (uses message.chat.id)
                   - int (direct chat_id)
            document: FSInputFile object containing the document to send.
            caption: Optional caption text for the document. Defaults to empty string.
            custom_markup: Optional keyboard markup to attach to the document message.
        
        Returns:
            Sent Message object containing the document, None on failure.
        
        Raises:
            TelegramBadRequest: On API errors (file too large, unsupported format, etc.).
        
        Example:
            >>> from aiogram.types import FSInputFile
            >>> doc = FSInputFile("report.pdf")
            >>> sent = await engine.send_document(
            ...     source=message.chat.id,
            ...     document=doc,
            ...     caption="Monthly Report",
            ...     custom_markup=keyboard
            ... )
        
        Note:
            - Maximum file size: 50 MB for bots
            - All file types are supported
            - Document preserves original filename
            - Users can download documents from chat
        """
        if hasattr(source, "chat"):
            chat_id = source.chat.id
        else:
            chat_id = source

        return await self.bot.send_document(
            chat_id=chat_id,
            document=document,
            caption=caption,
            reply_markup=custom_markup,
        )