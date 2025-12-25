# -*- coding: utf-8 -*-
from aiogram import Bot
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
    ReplyKeyboardMarkup
)

from .logger import get_logger

from .decorators import with_error_logging
from aiogram.exceptions import TelegramBadRequest

logger = get_logger()


class SmartMessage:
    def __init__(
        self,
        text: str | None = None,
        caption: str | None = None,
        photo: FSInputFile | str | None = None,
        reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
    ):
        self.text = text
        self.caption = caption
        self.photo = photo
        self.reply_markup = reply_markup


class MessageEngine:
    def __init__(self, bot: Bot):
        self.bot = bot

    @with_error_logging(logger=logger)
    async def send_smart_message(
        self,
        source: Message | CallbackQuery | int,
        msg: SmartMessage,
        raise_errors: bool = True,
        extra_kb: list[dict] | None = None,
    ):
        """
        Отправляет "умное" сообщение, которое может содержать текст, фото и клавиатуру.
        :param source: Исходный объект (Message, CallbackQuery или chat_id)
        :param msg: Объект SmartMessage с содержимым сообщения
        :param raise_errors: Флаг для поднятия исключений при ошибках
        """
        if isinstance(source, int):
            chat_id = source
        else:
            message = (
                source.message if isinstance(source, CallbackQuery) else source
            )
            chat_id = message.chat.id

        sent_message = None

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
    

    @with_error_logging(logger=logger)
    async def edit_smart_message(
        self, source: Message | CallbackQuery, msg: SmartMessage, extra_kb: list[dict] | None = None
    ):
        """
        Редактирует существующее сообщение с возможностью обновления фото, подписи или текста.
        :param source: Исходный объект (Message или CallbackQuery)
        :param msg: Объект SmartMessage с новым содержимым
        """
        message = source.message if isinstance(source, CallbackQuery) else source
        
        message = (
            source.message if isinstance(source, CallbackQuery) else source
        )

        chat_id = message.chat.id

        message_id = message.message_id

        edited_message = None

        try:
            if msg.photo:
                edited_message = await self.bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=message_id,
                    media=InputMediaPhoto(
                        media=msg.photo, caption=msg.caption or msg.text
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
                await source.answer("Информация обновлена.")
                return message
            elif "BUTTON_USER_PRIVACY_RESTRICTED" in error_str:
                await source.answer("Контакт не имеет юзернейм.")
                return None
            else:
                logger.exception(f"Unhandled TelegramBadRequest: {error_str}")
                raise

    @with_error_logging(logger=logger)
    async def reply_smart_message(
        self,
        source: Message,
        msg: SmartMessage,
        raise_errors: bool = True,
        extra_kb: list[dict] | None = None,
    ):
        """
        Отправляет "умное" сообщение в ответ на другое сообщение, которое может содержать текст, фото и клавиатуру.
        :param source: Исходный объект Message, на который отвечаем
        :param msg: Объект SmartMessage с содержимым сообщения
        :param raise_errors: Флаг для поднятия исключений при ошибках
        """
        sent_message = None

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
    
    async def send_document(
        self,
        source: Message | int,
        document: FSInputFile,
        caption: str = "",
        custom_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
        extra_kb: list[dict] | None = None,
    ):
        """
        Асинхронно отправляет документ в чат.
        """        
        if hasattr(source, "chat"):
            chat_id = source.chat.id
        else:
            chat_id = source

        if custom_markup:
            return await self.bot.send_document(
                chat_id=chat_id,
                document=FSInputFile(document),
                caption=caption,
                reply_markup=custom_markup
            )
        else:
            return await self.bot.send_document(
                chat_id=chat_id,
                document=FSInputFile(document),
                caption=caption,
            )
        
    
