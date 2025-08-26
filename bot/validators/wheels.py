# Валидаторы, характерные для дисков (PCD и т.п.)
import re

def is_pcd(text: str) -> bool:
    """
    PCD формата 5x112 или 5X114.3 (пробелы допускаются).
    """
    s = str(text).strip()
    return re.match(r"^\d+\s*[xX]\s*\d+(\.\d+)?$", s) is not None
