import re

def is_vin(s: str) -> bool:
    """
    Проверка VIN:
    - Ровно 17 символов
    - Допускаются только A–Z (кроме I, O, Q) и цифры 0–9
    """
    s = (s or "").strip().upper()
    return bool(re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", s))
