# Это "карта диалога" (сценарий), как бот разговаривает с пользователем.
# По сути это обычный словарь (dict) в Python.
# Ключ — имя узла (шага), значение — настройки этого шага:
#   - text:     какой текст отправлять
#   - buttons:  какие кнопки показать (если нужны)
#   - expect:   что ждём от пользователя ("text" — ввод текста)
#   - var_name: в какую переменную сохранить ответ пользователя
#   - validator: имя функции-валидатора (будет вызвана в коде бота)
#   - action:   имя "действия" (функции), которое выполнить на этом шаге
#   - next:     следующий узел (линейный переход)
#   - next_by_button: переходы по кнопкам (словарь "текст кнопки" -> "узел")

from .questions import TEXT, BUTTONS  # импортируем тексты и кнопки (данные)

FLOW = {
    # --- Стартовый узел ---
    "start": {
        "text": TEXT["greet"],
        "buttons": BUTTONS["start"],
        "next_by_button": {
            "Знаю размер": "ask_size",
            "Подобрать по авто": "ask_car_make",
        },
    },

    # === Ветка A: пользователь знает размер ===
    "ask_size": {
        "text": TEXT["ask_size"],
        "expect": "text",            # ждём текст
        "var_name": "size_raw",      # сохраняем ответ в ctx["size_raw"]
        "validator": "is_tire_size", # проверим формат размера
        "next": "ask_season",        # успешно — идём дальше
    },

    # === Ветка B: подбор по автомобилю ===
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

    # Если марки нет в кнопках — попросим ввести вручную
    "ask_car_make_free": {
        "text": TEXT["ask_car_make_free"],
        "expect": "text",
        "var_name": "car_make",
        "validator": "is_nonempty",
        "next": "ask_car_model_free",
    },

    # Toyota → модели
    "ask_car_model_Toyota": {
        "text": TEXT["ask_car_model_toyota"],
        "buttons": BUTTONS["toyota_models"],
        # любую модель, кроме "Другая", ведём к выбору года
        "next_by_button": {m: "ask_car_year" for m in BUTTONS["toyota_models"]},
    },

    # Volkswagen → модели
    "ask_car_model_VW": {
        "text": TEXT["ask_car_model_vw"],
        "buttons": BUTTONS["vw_models"],
        "next_by_button": {m: "ask_car_year" for m in BUTTONS["vw_models"]},
    },

    # BMW → модели
    "ask_car_model_BMW": {
        "text": TEXT["ask_car_model_bmw"],
        "buttons": BUTTONS["bmw_models"],
        "next_by_button": {m: "ask_car_year" for m in BUTTONS["bmw_models"]},
    },

    # Если модель "Другая" — просим ввести вручную
    "ask_car_model_free": {
        "text": TEXT["ask_car_model_free"],
        "expect": "text",
        "var_name": "car_model",
        "validator": "is_nonempty",
        "next": "ask_car_year",
    },

    # Год выпуска авто
    "ask_car_year": {
        "text": TEXT["ask_car_year"],
        "expect": "text",
        "var_name": "car_year",
        "validator": "is_year",
        "next": "resolve_oem_size",
    },

    # Находим штатный размер (action должна записать ctx["size_raw"])
    "resolve_oem_size": {
        "text": TEXT["resolving_oem"],
        "action": "find_oem_size",  # функцию реализуем в actions.py
        "next": "ask_season",
    },

    # === Общая ветка (и для A, и для B) ===
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

    # Ищем предложения (action должна записать ctx["offers"] = [...])
    "search_offers": {
        "text": TEXT["searching"],
        "action": "search_tires",  # реализуем в actions.py
        "next": "show_offers",
    },

    # Печатаем найденные варианты (action выводит карточки и т.д.)
    "show_offers": {
        "text": TEXT["found_offers"],
        "action": "render_offers",  # реализуем в actions.py
        "next": "end",
    },

    # Финал
    "end": {
        "text": TEXT["end"],
    },
}