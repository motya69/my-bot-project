# Реэкспорт "витрины" валидаторов для удобных импортов.
from .base import is_nonempty, is_year, is_number
from .tires import is_tire_size
from .wheels import is_pcd
from .vin import is_vin   # если у тебя есть отдельный файл vin.py, иначе оставь здесь функцию

__all__ = [
    "is_nonempty",
    "is_year",
    "is_number",
    "is_tire_size",
    "is_pcd",
    "is_vin",
]