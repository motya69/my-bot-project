from ..common import TEXT as C_TEXT, BUTTONS as C_BTN
from .questions import TEXT_T, BUTTONS_T

FLOW = {
    # t_entry — вход в ветку шин
    "t_entry": {
        "text": TEXT_T["entry"],
        "buttons": BUTTONS_T["entry"],
        "next_by_button": {
            "Знаю размер": "t_ask_size",
            "Подобрать по авто": "t_ask_car_make",
        },
    },

    # знаю размер
    "t_ask_size": {
        "text": TEXT_T["ask_size"],
        "expect": "text",
        "var_name": "size_raw",
        "validator": "is_tire_size",
        "next": "t_ask_season",
    },

    # подбор по авто: марка/модель/год → action найдет размер
    "t_ask_car_make": {
        "text": C_TEXT["ask_car_make"],
        "buttons": C_BTN["car_makes"],
        "next_by_button": {
            "Toyota": "t_ask_car_model_Toyota",
            "Volkswagen": "t_ask_car_model_VW",
            "BMW": "t_ask_car_model_BMW",
            "Другая": "t_ask_car_make_free",
        },
    },
    "t_ask_car_make_free": {
        "text": C_TEXT["ask_car_make_free"],
        "expect": "text",
        "var_name": "car_make",
        "validator": "is_nonempty",
        "next": "t_ask_car_model_free",
    },
    "t_ask_car_model_Toyota": {
        "text": C_TEXT["ask_car_model_toyota"],
        "buttons": C_BTN["toyota_models"],
        "next_by_button": {m: "t_ask_car_year" for m in C_BTN["toyota_models"]},
    },
    "t_ask_car_model_VW": {
        "text": C_TEXT["ask_car_model_vw"],
        "buttons": C_BTN["vw_models"],
        "next_by_button": {m: "t_ask_car_year" for m in C_BTN["vw_models"]},
    },
    "t_ask_car_model_BMW": {
        "text": C_TEXT["ask_car_model_bmw"],
        "buttons": C_BTN["bmw_models"],
        "next_by_button": {m: "t_ask_car_year" for m in C_BTN["bmw_models"]},
    },
    "t_ask_car_model_free": {
        "text": C_TEXT["ask_car_model_free"],
        "expect": "text",
        "var_name": "car_model",
        "validator": "is_nonempty",
        "next": "t_ask_car_year",
    },
    "t_ask_car_year": {
        "text": C_TEXT["ask_car_year"],
        "expect": "text",
        "var_name": "car_year",
        "validator": "is_year",
        "next": "t_resolve_oem_size",
    },
    "t_resolve_oem_size": {
        "text": TEXT_T["resolving_oem"],
        "action": "find_oem_size",
        "next": "t_ask_season",
    },

    # общая развилка по шинам
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
        # явная кнопка для возврата
        "buttons": ["⬅️ Вернуться к выбору бюджета"],
        "next_by_button": {
            "⬅️ Вернуться к выбору бюджета": "t_ask_budget"
        },
    }
}
