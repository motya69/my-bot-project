from ..common import TEXT as C_TEXT, BUTTONS as C_BTN
from .questions import TEXT_T, BUTTONS_T

FLOW = {
    "t_entry": {
        "text": TEXT_T["entry"],
        "buttons": [
            "Знаю размер",
            "🧠 Умный подбор (по шагам)",
            "Подобрать по авто",
            "🔑 По VIN",
        ],
        "next_by_button": {
            "Знаю размер": "t_ask_size",
            "🧠 Умный подбор (по шагам)": "t_smart_width",
            "Подобрать по авто": "t_ask_car_make",
            "🔑 По VIN": "t_vin",
        },
    },

    "t_ask_size": {
        "text": TEXT_T["ask_size"],
        "expect": "text",
        "var_name": "size_raw",
        "validator": "is_tire_size",
        "next": "t_ask_season",
    },

    # ... (узлы подбора по авто t_ask_car_* ... t_resolve_oem_size) ...

    "t_ask_season": {
        "text": TEXT_T["ask_season"],
        "buttons": BUTTONS_T["season"],
        "next_by_button": {b: "t_ask_budget" for b in BUTTONS_T["season"]},
    },
    "t_ask_budget": {
        "text": TEXT_T["ask_budget"],
        "buttons": BUTTONS_T["budget"] + ["📊 Сравнение сегментов"],
        "next_by_button": {b: "t_ask_brand" for b in BUTTONS_T["budget"]},
    },
    "t_ask_brand": {
        "text": TEXT_T["ask_brand"],
        "buttons": BUTTONS_T["brands"],
        "next_by_button": {b: "t_search_offers" for b in BUTTONS_T["brands"]},
    },
    "t_search_offers": {
        "text": TEXT_T["searching"],
        "action": "search_tires",
        "next": "t_show_offers",
    },
    "t_show_offers": {
        "text": TEXT_T["found_offers"],
        "action": "render_tire_offers",
        "next": "end",
    },
    "t_budget_compare": {
        "text": TEXT_T["budget_compare"],
        "buttons": ["⬅️ Вернуться к выбору бюджета"],
        "next_by_button": {
            "⬅️ Вернуться к выбору бюджета": "t_ask_budget"
        },
    },  # ← ВАЖНО: ЗАКРЫЛИ t_budget_compare и поставили запятую!

    # ---------- УМНЫЙ ПОДБОР (ОТДЕЛЬНЫЕ ВЕРХНЕУРОВНЕВЫЕ УЗЛЫ) ----------
    "t_smart_width": {
        "text": "Выбери ширину шины:",
        "buttons": [],           # заполним динамически в main
        "next_by_button": {},    # обработаем вручную в main
    },
    "t_smart_height": {
        "text": "Выбери профиль (высоту, %):",
        "buttons": [],
        "next_by_button": {},
    },
    "t_smart_diameter": {
        "text": "Выбери диаметр (дюймы):",
        "buttons": [],
        "next_by_button": {},
    },

    # ---------- VIN ----------
    "t_vin": {
        "text": "Введи VIN (17 символов, латиница/цифры, без I,O,Q):",
        "expect": "text",
        "validator": "is_vin",
        "var_name": "vin",
        "next": "t_vin_sizes",
    },
    "t_vin_sizes": {
        "text": "По VIN доступны такие размеры. Выбери один:",
        "buttons": ["205/55 R16", "215/60 R16", "225/45 R17"],
        "next_by_button": {s: "t_ask_season" for s in ["205/55 R16", "215/60 R16", "225/45 R17"]},
    },
}
