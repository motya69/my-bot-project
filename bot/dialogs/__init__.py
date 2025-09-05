# bot/dialogs/__init__.py

# Общие тексты/кнопки (для стартового выбора "Шины / Диски")
from .common.questions import TEXT as C_TEXT, BUTTONS as C_BTN

# Ветки
from .tires import TIRES_FLOW          # содержит t_entry, t_smart_*, t_ask_*, ...
from .wheels import WHEELS_FLOW        # содержит w_entry, w_ask_*, ...

# ----- ЕДИНСТВЕННЫЙ start (общий экран выбора сущности) -----
START_NODE = {
    "start": {
        "text": C_TEXT["greet"],            # например: "Привет! Чем помочь сегодня?"
        "buttons": C_BTN["entity"],         # ["Шины", "Диски"]
        "next_by_button": {
            "Шины": "t_entry",
            "Диски": "w_entry",
        },
    }
}

# ----- СБОРКА ИТОГОВОГО FLOW -----
FLOW = {}
FLOW.update(START_NODE)    # общий старт
FLOW.update(TIRES_FLOW)    # вся шинная ветка (включая t_smart_width)
FLOW.update(WHEELS_FLOW)   # вся дисковая ветка

# Диагностика (увидишь в логе при запуске)
print("[FLOW] keys:", len(FLOW), "t_smart_width in FLOW:", "t_smart_width" in FLOW, flush=True)
