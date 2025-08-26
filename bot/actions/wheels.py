# Действия для ветки "Диски"
from .common import render_cards

def find_oem_wheels(bot, chat_id, ctx):
    """
    Заглушка: подбираем параметры дисков по авто (марка/модель/год).
    """
    model = ctx.get("car_model", "")
    # Пример параметров (замени логикой/БД)
    params = {"wheel_r": "17", "wheel_j": "7.0", "wheel_pcd": "5x114.3", "wheel_et": "45", "wheel_dia": "60.1"}
    if "Camry" in model:
        params["wheel_r"] = "17"
    ctx.update(params)

    bot.send_message(
        chat_id,
        f"Рекомендация по авто:\nR{params['wheel_r']}, {params['wheel_j']}J, "
        f"{params['wheel_pcd']}, ET{params['wheel_et']}, DIA {params['wheel_dia']}"
    )

def search_wheels(bot, chat_id, ctx):
    """
    Ищем диски по параметрам (заглушка).
    """
    p = lambda k: ctx.get(k, "?")
    spec = f"R{p('wheel_r')} {p('wheel_j')}J {p('wheel_pcd')} ET{p('wheel_et')} DIA {p('wheel_dia')}"
    ctx["wheel_offers"] = [
        {"title": "Replay FD110", "subtitle": spec, "price": "110 € / шт", "stock": 8, "url": "https://shop/wheels/1"},
        {"title": "X-Race XR-092", "subtitle": spec, "price": "95 € / шт",  "stock": 12,"url": "https://shop/wheels/2"},
        {"title": "RIAL Lugano",   "subtitle": spec, "price": "150 € / шт", "stock": 5, "url": "https://shop/wheels/3"},
    ]

def render_wheels_offers(bot, chat_id, ctx):
    render_cards(bot, chat_id, ctx.get("wheel_offers", []), empty_text="По дискам ничего не нашлось.")
