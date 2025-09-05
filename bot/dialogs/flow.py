# bot/dialogs/flow.py
# Карта диалога (общая, без шинного start внутри других модулей)

from bot.dialogs.common.questions import TEXT, BUTTONS

FLOW = {
    # --- Стартовый узел (общий) ---
    "start": {
        "text": TEXT["greet"],
        "buttons": [
            "Знаю размер",
            "🧠 Умный подбор (по шагам)",
            "Подобрать по авто",
            "🔑 По VIN",
        ],
        "next_by_button": {
            "Знаю размер": "t_ask_size",
            "Подобрать по авто": "t_ask_car_make",
            "🧠 Умный подбор (по шагам)": "t_smart_width",  # если используешь умный режим
            "🔑 По VIN": "t_vin",
        },
    },

    # === Ветка A: пользователь знает размер ===
    "ask_size": {
        "text": TEXT["ask_size"],
        "expect": "text",
        "var_name": "size_raw",
        "validator": "is_tire_size",
        "next": "ask_season",
    },

    # === Ветка B: подбор по авто ===
    "ask_car_make": {
        "text": TEXT["ask_car_make"],
        "buttons": BUTTONS["car_makes"],
        "next_by_button": {
            "Toyota": "ask_car_model_Toyota",
            "Volkswagen": "ask_car_model_VW",
            "BMW": "ask_car_model_BMW",
            "Другая": "ask_car_make_free",
        },
    },

    "ask_car_make_free": {
        "text": TEXT["ask_car_make_free"],
        "expect": "text",
        "var_name": "car_make",
        "validator": "is_nonempty",
        "next": "ask_car_model_free",
    },

    "ask_car_model_Toyota": {
        "text": TEXT["ask_car_model_toyota"],
        "buttons": BUTTONS["toyota_models"],
        "next_by_button": {m: "ask_car_year" for m in BUTTONS["toyota_models"]},
    },

    "ask_car_model_VW": {
        "text": TEXT["ask_car_model_vw"],
        "buttons": BUTTONS["vw_models"],
        "next_by_button": {m: "ask_car_year" for m in BUTTONS["vw_models"]},
    },

    "ask_car_model_BMW": {
        "text": TEXT["ask_car_model_bmw"],
        "buttons": BUTTONS["bmw_models"],
        "next_by_button": {m: "ask_car_year" for m in BUTTONS["bmw_models"]},
    },

    "ask_car_model_free": {
        "text": TEXT["ask_car_model_free"],
        "expect": "text",
        "var_name": "car_model",
        "validator": "is_nonempty",
        "next": "ask_car_year",
    },

    "ask_car_year": {
        "text": TEXT["ask_car_year"],
        "expect": "text",
        "var_name": "car_year",
        "validator": "is_year",
        "next": "resolve_oem_size",
    },

    "resolve_oem_size": {
        "text": TEXT["resolving_oem"],
        "action": "find_oem_size",
        "next": "ask_season",
    },

    # === Общая ветка после получения размера ===
    "ask_season": {
        "text": TEXT["ask_season"],
        "buttons": BUTTONS["season"],
        "next_by_button": {b: "ask_budget" for b in BUTTONS["season"]},
    },

    "ask_budget": {
        "text": TEXT["ask_budget"],
        "buttons": BUTTONS["budget"],
        "next_by_button": {b: "ask_brand_pref" for b in BUTTONS["budget"]},
    },

    "ask_brand_pref": {
        "text": TEXT["ask_brand"],
        "buttons": BUTTONS["brands"],
        "next_by_button": {b: "search_offers" for b in BUTTONS["brands"]},
    },

    "search_offers": {
        "text": TEXT["searching"],
        "action": "search_tires",
        "next": "show_offers",
    },

    "show_offers": {
        "text": TEXT["found_offers"],
        "action": "render_tire_offers",
        "next": "end",
    },

    "end": {
        "text": TEXT["end"],
    },

    # === РЕЖИМ 4: По VIN ===
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
        "next_by_button": {s: "ask_season" for s in ["205/55 R16","215/60 R16","225/45 R17"]},
    },

    # === РЕЖИМ 2: Умный подбор (демо) ===
    "t_smart_width": {
        "text": "Выбери ширину шины:",
        "buttons": ["185","195","205","215","225","235","245","255"],
        "next_by_button": {w: "t_smart_height" for w in ["185","195","205","215","225","235","245","255"]},
    },
    "t_smart_height": {
        "text": "Выбери профиль (высоту, %):",
        "buttons": ["45","50","55","60","65","70"],
        "next_by_button": {h: "t_smart_diameter" for h in ["45","50","55","60","65","70"]},
    },
    "t_smart_diameter": {
        "text": "Выбери диаметр (дюймы):",
        "buttons": ["14","15","16","17","18","19","20"],
        "next_by_button": {d: "ask_season" for d in ["14","15","16","17","18","19","20"]},
    },
}
