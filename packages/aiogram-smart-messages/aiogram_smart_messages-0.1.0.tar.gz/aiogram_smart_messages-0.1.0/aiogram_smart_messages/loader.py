# -*- coding: utf-8 -*-
import json
from pathlib import Path
from typing import Dict


def load_message_json(
    namespace: str,
    role: str,
    lang: str,
    filename: str,
    module: str = "sotamaker",
    use_cache: bool = True,
) -> Dict:
    """
    Загружает JSON-файл сообщений из указанного модуля (sotamaker или templates).

    Args:
        namespace (str): Название приложения или шаблона (например, 'game_stars_bot', 'horoscope_bot').
        role (str): Роль (Пример: admin/user/common).
        lang (str): Код языка (например, 'ru').
        filename (str): Имя JSON-файла (например, 'start.json').
        module (str): Модуль, где искать файл ('sotamaker' или 'templates'). По умолчанию 'sotamaker'.
        use_cache (bool): Использовать кэширование. По умолчанию True.

    Returns:
        Dict: Содержимое JSON-файла.

    Raises:
        FileNotFoundError: Если файл не найден.
    """
    if namespace:
        path = Path(f"{module}/{namespace}/messages/{role}/{lang}/{filename}")
    else:
        path = Path(f"{module}/messages/{role}/{lang}/{filename}")

    if not path.exists():
        raise FileNotFoundError(f"Файл {path} не найден.")

    if use_cache:
        return _load_cached_message_json(str(path))
    else:
        with path.open(encoding="utf-8") as file:
            return json.load(file)


# @lru_cache(maxsize=128)
def _load_cached_message_json(path_str: str) -> Dict:
    """
    Кэшированная загрузка JSON-файла.

    Args:
        path_str (str): Путь к файлу.

    Returns:
        Dict: Содержимое JSON-файла.
    """
    path = Path(path_str)
    with path.open(encoding="utf-8") as file:
        return json.load(file)
