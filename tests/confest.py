# tests/conftest.py
import os, sys

# Добавляем КОРЕНЬ ПРОЕКТА (папку, где лежит bot/) в sys.path,
# чтобы 'from bot ...' работал при обычном 'pytest -q'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
