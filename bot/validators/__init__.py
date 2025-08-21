# Этот файл делает папку validators полноценным Python-пакетом.
# Здесь мы укажем, какие функции можно импортировать "снаружи".

from .validators import is_nonempty, is_year, is_tire_size

# Если кто-то напишет:
#   from bot.validators import is_tire_size
# то функция подтянется из validators.py без лишних путей.

__all__ = ["is_nonempty", "is_year", "is_tire_size"]