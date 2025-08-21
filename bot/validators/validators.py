# Здесь функции проверки ввода пользователя
# (валидация помогает отсеять "мусорный" ввод).

import re

def is_nonempty(text: str) -> bool:
    """Проверяет, что строка не пустая."""
    return bool(text and text.strip())

def is_year(text: str) -> bool:
    """Проверяет, что введён год (от 1980 до 2035)."""
    if not text.isdigit():
        return False
    year = int(text)
    return 1980 <= year <= 2035

def is_tire_size(text: str) -> bool:
    """
    Проверяет, что строка похожа на размер шины.
    Пример: 205/55 R16 или 195/65R15.
    """
    pattern = r"^\d{3}/\d{2}\s?R\d{2}$"
    return re.match(pattern, text.strip().upper()) is not None