# bot/dialogs/wheels/flow.py
from ..common.questions import TEXT as C_TEXT, BUTTONS as C_BTN
from .questions import TEXT_W, BUTTONS_W
print("[DEBUG wheels.questions TEXT_W keys]:", list(TEXT_W.keys()), flush=True)
print("[DEBUG wheels.questions BUTTONS_W keys]:", list(BUTTONS_W.keys()), flush=True)
FLOW = {
    # Вход в ветку дисков
    "w_entry": {
        "text": TEXT_W["entry"],
        "buttons": [
            "Знаю параметры",
            "🧠 Умный подбор (по шагам)",   # ← ДОБАВИЛИ
            "Подобрать по авто",
            "🔑 По VIN",
        ],
        "next_by_button": {
            "Знаю параметры": "w_ask_r",
            "🧠 Умный подбор (по шагам)": "w_smart_r",  # ← ДОБАВИЛИ
            "Подобрать по авто": "w_ask_car_make",
            "🔑 По VIN": "w_vin",
        },
    },
    "w_vin": {
        "text": "Введи VIN (17 символов, латиница/цифры, без I,O,Q):",
        "expect": "text",
        "validator": "is_vin",
        "var_name": "vin",
        "action": "wheels_params_from_vin",   # ← экшен заполнит ctx["wheel_options"]
        "next": "w_vin_params",
    },
    "w_vin_params": {
        "text": "Нашёл такие варианты параметров дисков. Выбери один:",
        "buttons": [],          # динамика из ctx["wheel_options"]
        # дальше пойдём руками в on_button → на w_ask_budget
    # Знаю параметры → по очереди спрашиваем поля
    "w_ask_r": {
        "text": TEXT_W["ask_r"],
        "expect": "text",
        "var_name": "wheel_r",
        "validator": "is_number",
        "next": "w_ask_j",
    },
    "w_ask_j": {
        "text": TEXT_W["ask_j"],
        "expect": "text",
        "var_name": "wheel_j",
        "validator": "is_number",
        "next": "w_ask_pcd",
    },
    "w_ask_pcd": {
        "text": TEXT_W["ask_pcd"],
        "expect": "text",
        "var_name": "wheel_pcd",
        "validator": "is_pcd",
        "next": "w_ask_et",
    },
    "w_ask_et": {
        "text": TEXT_W["ask_et"],
        "expect": "text",
        "var_name": "wheel_et",
        "validator": "is_number",
        "next": "w_ask_dia",
    },
    "w_ask_dia": {
        "text": TEXT_W["ask_dia"],
        "expect": "text",
        "var_name": "wheel_dia",
        "validator": "is_number",
        "next": "w_ask_budget",
    },

    # Подбор по авто (используем общие списки марок/моделей)
    "w_ask_car_make": {
        "text": C_TEXT["ask_car_make"],
        "buttons": C_BTN["car_makes"],
        "next_by_button": {
            "Toyota": "w_ask_car_model_Toyota",
            "Volkswagen": "w_ask_car_model_VW",
            "BMW": "w_ask_car_model_BMW",
            "Другая": "w_ask_car_make_free",
        },
    },
    "w_ask_car_make_free": {
        "text": C_TEXT["ask_car_make_free"],
        "expect": "text",
        "var_name": "car_make",
        "validator": "is_nonempty",
        "next": "w_ask_car_model_free",
    },
    "w_ask_car_model_Toyota": {
        "text": C_TEXT["ask_car_model_toyota"],
        "buttons": C_BTN["toyota_models"],
        "next_by_button": {m: "w_ask_car_year" for m in C_BTN["toyota_models"]},
    },
    "w_ask_car_model_VW": {
        "text": C_TEXT["ask_car_model_vw"],
        "buttons": C_BTN["vw_models"],
        "next_by_button": {m: "w_ask_car_year" for m in C_BTN["vw_models"]},
    },
    "w_ask_car_model_BMW": {
        "text": C_TEXT["ask_car_model_bmw"],
        "buttons": C_BTN["bmw_models"],
        "next_by_button": {m: "w_ask_car_year" for m in C_BTN["bmw_models"]},
    },
    "w_ask_car_model_free": {
        "text": C_TEXT["ask_car_model_free"],
        "expect": "text",
        "var_name": "car_model",
        "validator": "is_nonempty",
        "next": "w_ask_car_year",
    },
    "w_ask_car_year": {
        "text": C_TEXT["ask_car_year"],
        "expect": "text",
        "var_name": "car_year",
        "validator": "is_year",
        "next": "w_resolve_oem_wheels",
    },
    "w_resolve_oem_wheels": {
        "text": TEXT_W["resolving_oem"],
        "action": "find_oem_wheels",
        "next": "w_ask_budget",
    },
    # ── Умный подбор дисков ──
    "w_smart_r": {
        "text": "Выбери диаметр (R):",
        "buttons": [],  # динамически
        "next_by_button": {},
    },
    "w_smart_j": {
        "text": "Выбери ширину обода (J):",
        "buttons": [],
        "next_by_button": {},
    },
    "w_smart_pcd": {
        "text": "Выбери PCD:",
        "buttons": [],
        "next_by_button": {},
    },
    "w_smart_et": {
        "text": "Выбери вылет (ET):",
        "buttons": [],
        "next_by_button": {},
    },
    "w_smart_dia": {
        "text": "Выбери DIA (ЦО):",
        "buttons": [],
        "next_by_button": {},
    },

    # Бюджет и бренды → поиск/вывод
    "w_ask_budget": {
        "text": TEXT_W["ask_budget"],
        "buttons": BUTTONS_W["budget"],
        "next_by_button": {b: "w_ask_brand" for b in BUTTONS_W["budget"]},
    },
    "w_ask_brand": {
        "text": TEXT_W["ask_brand"],
        "buttons": BUTTONS_W["brands"],
        "next_by_button": {b: "w_search_offers" for b in BUTTONS_W["brands"]},
    },
    "w_search_offers": {
        "text": TEXT_W["searching"],
        "action": "search_wheels",
        "next": "w_show_offers",
    },
    "w_show_offers": {
        "text": TEXT_W["found_offers"],
        "action": "render_wheels_offers",
        "next": "end",   # общий финал из базового FLOW
    },
}}
