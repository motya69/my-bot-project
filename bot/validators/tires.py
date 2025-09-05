import re

def is_tire_size(text: str) -> bool:
    """
    Допускаем форматы: '205/55R16', '205/55 R16', любые лишние пробелы.
    """
    if not text:
        return False

    s = str(text).upper().strip()
    # 1) нормализуем пробелы вокруг R: 'R', ' R', '  R ' -> ' R '
    s = re.sub(r"\s*R\s*", " R", s)
    # 2) сжимаем возможные двойные пробелы
    s = re.sub(r"\s+", " ", s).strip()

    # 205/55 R16
    pattern = r"^\d{3}/\d{2}\sR\d{2}$"
    return re.match(pattern, s) is not None

def is_vin(s: str) -> bool:
    s = (s or "").strip().upper()
    return bool(re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", s))