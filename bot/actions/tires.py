# Действия для ветки "Шины"
from .common import render_cards

def find_oem_size(bot, chat_id, ctx):
    """
    Заглушка: находим штатный размер шин по авто (марка/модель/год).
    В реальности тут обращение к БД или API.
    """
    make  = ctx.get("car_make", "Unknown")
    model = ctx.get("car_model", "Unknown")
    year  = ctx.get("car_year", "????")

    # пример рекомендованного размера
    size = "205/55 R16"
    ctx["size_raw"] = size

    bot.send_message(chat_id, f"Для {make} {model} {year} подходит размер <b>{size}</b>.", parse_mode="HTML")

def search_tires(bot, chat_id, ctx):
    """
    Ищем шины по: size_raw, season, budget, brand_pref (пока — заглушка).
    """
    size = ctx.get("size_raw", "?")
    season = ctx.get("season", "?")
    budget = ctx.get("budget", "?")
    brand_pref = ctx.get("brand_pref", "Без разницы")

    # Заглушечные варианты (подменишь API вызовом)
    ctx["tire_offers"] = [
        {"title": f"Michelin Primacy 4 ({size})",
         "subtitle": f"{season}, {budget}, бренд: {brand_pref}",
         "price": "12 000 ₽", "stock": 8, "url": "https://shop/tires/1"},
        {"title": f"Continental PremiumContact 6 ({size})",
         "subtitle": f"{season}, {budget}, бренд: {brand_pref}",
         "price": "11 500 ₽", "stock": 12, "url": "https://shop/tires/2"},
        {"title": f"Nokian Hakka Green 3 ({size})",
         "subtitle": f"{season}, {budget}, бренд: {brand_pref}",
         "price": "9 500 ₽", "stock": 5, "url": "https://shop/tires/3"},
    ]

def render_tire_offers(bot, chat_id, ctx):
    render_cards(bot, chat_id, ctx.get("tire_offers", []), empty_text="По шинам ничего не нашлось.")
