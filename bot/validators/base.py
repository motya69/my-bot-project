# Общие валидаторы, которые полезны в обеих ветках.

def is_nonempty(text: str) -> bool:
    """Строка не пустая."""
    return bool(text and str(text).strip())

def is_year(text: str) -> bool:
    """Год в разумных границах (1980–2035)."""
    s = str(text).strip()
    if not s.isdigit():
        return False
    y = int(s)
    return 1980 <= y <= 2035

def is_number(text: str) -> bool:
    """Целое или десятичное число: 17 / 7.5 / 60.1"""
    s = str(text).strip().replace(",", ".")
    try:
        float(s)
        return True
    except Exception:
        return False
