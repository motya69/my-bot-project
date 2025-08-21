"""
Пакет dialogs — хранит сценарий диалогов и тексты.
- flow.py      — карта переходов (узлы диалога)
- questions.py — тексты сообщений, кнопки, справочники
"""

from .flow import FLOW
from .questions import TEXT, BUTTONS, BRAND_TIERS, SEASONS

__all__ = ["FLOW", "TEXT", "BUTTONS", "BRAND_TIERS", "SEASONS"]