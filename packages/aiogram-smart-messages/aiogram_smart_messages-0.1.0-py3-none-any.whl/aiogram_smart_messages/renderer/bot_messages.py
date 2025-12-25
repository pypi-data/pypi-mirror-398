# -*- coding: utf-8 -*-
import os

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
    Класс для загрузки, парсинга и отправки "умных" сообщений,
    которые могут содержать текст, фото и кнопки, с поддержкой локализации и форматирования.
    """

    @staticmethod
    @with_error_logging(logger=logger)
    def load_json(
        namespace: str,
        role: str,
        lang: str,
        menu_file: str,
        block_key: str,
        context: dict,
        module: str = "main_bot",
    ) -> dict:
        """
        Загружает JSON с сообщением по заданным параметрам, извлекает нужный блок и форматирует текст и подписи.

        Args:
            namespace (str): Пространство имён для организации сообщений.
            role (str): Роль (Пример: admin/user/common).
            lang (str): Язык сообщения.
            menu_file (str): Имя файла меню (без расширения).
            block_key (str): Ключ блока в JSON для загрузки. Поддерживает вложенные ключи через точки.
            context (dict): Контекст для форматирования текста и подписи.

        Returns:
            dict: Словарь с данными блока сообщения, где текст и подписи отформатированы.
        """
        def deep_get(dictionary, keys, default=None):
            keys_list = keys.split(".")
            current = dictionary
            for key in keys_list:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            return current

        use_cache = not context
        data = load_message_json(
            namespace, role, lang, f"{menu_file}.json", module, use_cache=use_cache
        )
        block = deep_get(data, block_key) if block_key else data

        if block is None:
            raise ValueError(
                f"SmartMessageRenderer.load_json could not find block_key '{block_key}' in {namespace}/{menu_file}.json "
                f"(role={role}, lang={lang}). Check the JSON structure and key path."
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
    @with_error_logging(logger=logger)
    def parse_to_smart(
        block: dict,
        namespace: str,
        role: str,
        lang: str,
        custom_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
        module: str = "main_bot",
        extra_kb: list[dict] | None = None,
        extra_kb_position: str = "bottom",
    ) -> SmartMessage:
        """
        Преобразует блок данных сообщения в объект SmartMessage, загружая фото и создавая клавиатуру.

        Args:
            block (dict): Словарь с данными блока сообщения.
            namespace (str): Пространство имён для организации сообщений.
            lang (str): Язык сообщения.

        Returns:
            SmartMessage: Объект сообщения с текстом, фото и клавиатурой.
        """
        if block is None or not isinstance(block, dict):
            raise ValueError(
                f"SmartMessageRenderer.parse_to_smart received invalid block: {block!r}. "
                f"Most likely: block_key not found in JSON or JSON formatting error."
            )
        
        if extra_kb:
            if isinstance(extra_kb, list) and extra_kb and isinstance(extra_kb[0], dict):
                extra_kb = [extra_kb]

            # extra_kb теперь ожидается как list[list[buttons]]
            if "buttons" in block and isinstance(block["buttons"], list):
                if extra_kb_position == "top":
                    block["buttons"] = extra_kb + block["buttons"]
                else:
                    block["buttons"].extend(extra_kb)
            else:
                block["buttons"] = list(extra_kb)

        photo = block.get("photo")
        photo_file = None

        if photo:
            is_probably_file_id = isinstance(photo, str) and not any(
                c in photo for c in ["/", "\\", "."]
            )
            if is_probably_file_id:
                photo_file = photo  # Telegram file_id
            else:
                photo_path = f"{module}/{namespace}/photos/{role}/{lang}/{photo}"
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
    @with_error_logging(logger=logger)
    async def send(
        cls,
        engine: MessageEngine,
        source: Message | CallbackQuery,
        role: str,
        module: str = "main_bot",
        namespace: str | None = None,
        menu_file: str | None = None,
        block_key: str | None = None,
        lang: str = "ru",
        context: dict = None,
        custom_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
        override_block: dict = None,
        raise_errors: bool = False,
        extra_kb: list[dict] | None = None,
        extra_kb_position: str = "bottom",
    ):
        """
        Асинхронно отправляет "умное" сообщение в чат, используя MessageEngine.
        Можно передать override_block, чтобы не загружать JSON с файла.
        """
        context = context or {}

        if override_block is not None:
            block = override_block
        else:
            if not all([menu_file, block_key]):
                raise ValueError(
                    "namespace, menu_file, and block_key are required unless override_block is provided."
                )
            block = cls.load_json(
                namespace, role, lang, menu_file, block_key, context, module=module
            )
        msg = cls.parse_to_smart(
            block, namespace or "", role, lang, custom_markup, module, extra_kb=extra_kb, extra_kb_position=extra_kb_position
        )


        return await engine.send_smart_message(
            source=source, msg=msg, raise_errors=raise_errors
        )

    @classmethod
    @with_error_logging(logger=logger)
    async def edit(
        cls,
        engine: MessageEngine,
        source: Message | CallbackQuery,
        role: str,
        module: str = "main_bot",
        namespace: str | None = None,
        menu_file: str | None = None,
        block_key: str | None = None,
        lang: str = "ru",
        context: dict = None,
        custom_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
        override_block: dict = None,
        extra_kb: list[dict] | None = None,
        extra_kb_position: str = "bottom",
    ):
        """
        Асинхронно редактирует существующее сообщение. Можно передать override_block вместо загрузки JSON.
        """
        context = context or {}
        if override_block is not None:
            block = override_block
        else:
            if not all([menu_file, block_key]):
                raise ValueError(
                    "menu_file, and block_key are required unless override_block is provided."
                )
            block = cls.load_json(
                namespace, role, lang, menu_file, block_key, context, module
            )
        msg = cls.parse_to_smart(block, namespace or "", role, lang, custom_markup, extra_kb=extra_kb, extra_kb_position=extra_kb_position)
        return await engine.edit_smart_message(source=source, msg=msg)

    @classmethod
    @with_error_logging(logger=logger)
    async def smart_edit_or_send(
        cls,
        engine: MessageEngine,
        source: Message | CallbackQuery,
        role: str,
        module: str = "main_bot",
        namespace: str | None = None,
        menu_file: str | None = None,
        block_key: str | None = None,
        lang: str = "ru",
        context: dict = None,
        custom_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
        override_block: dict = None,
        extra_kb: list[dict] | None = None,
        extra_kb_position: str = "bottom",
    ):
        """
        Умно определяет, нужно ли редактировать сообщение или удалить и отправить заново (если есть медиа).
        """
        context = context or {}
        if override_block is not None:
            block = override_block
        else:
            if not all([menu_file, block_key]):
                raise ValueError(
                    "menu_file, and block_key are required unless override_block is provided."
                )
            block = cls.load_json(
                namespace, role, lang, menu_file, block_key, context, module
            )

        msg = cls.parse_to_smart(block, namespace or "", role, lang, custom_markup, extra_kb=extra_kb, extra_kb_position=extra_kb_position)

        # Определение наличия медиа у исходного сообщения
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
    @with_error_logging(logger=logger)
    async def reply(
        cls,
        engine: MessageEngine,
        source: Message,
        role: str,
        module: str = "main_bot",
        namespace: str | None = None,
        menu_file: str | None = None,
        block_key: str | None = None,
        lang: str = "ru",
        context: dict = None,
        custom_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
        override_block: dict = None,
        raise_errors: bool = False,
        extra_kb: list[dict] | None = None,
        extra_kb_position: str = "bottom",
    ):
        """
        Асинхронно отправляет "умное" сообщение ответом на другое сообщение (reply).
        Можно передать override_block, чтобы не загружать JSON с файла.
        """
        context = context or {}

        if override_block is not None:
            block = override_block
        else:
            if not all([menu_file, block_key]):
                raise ValueError(
                    "namespace, menu_file, and block_key are required unless override_block is provided."
                )
            block = cls.load_json(
                namespace, role, lang, menu_file, block_key, context, module=module
            )

        msg = cls.parse_to_smart(
            block, namespace or "", role, lang, custom_markup, module, extra_kb=extra_kb, extra_kb_position=extra_kb_position
        )

        # Используем специальный метод движка для reply (если есть) или fallback
        if hasattr(engine, "reply_smart_message"):
            return await engine.reply_smart_message(source=source, msg=msg, raise_errors=raise_errors)
        else:
            # fallback — обычный reply через message.reply()
            return await source.reply(
                msg.text or msg.caption or "",
                reply_markup=msg.reply_markup,
                disable_web_page_preview=True,
            )
        

    @classmethod
    @with_error_logging(logger=logger)
    async def send_document(
        cls,
        engine: MessageEngine,
        source: Message | int,
        document: FSInputFile,
        caption: str = "",
        custom_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
    ):
        """
        Асинхронно отправляет документ в чат.
        """
        return await engine.send_document(
            source=source,
            document=document,
            caption=caption,
            custom_markup=custom_markup,
        )
