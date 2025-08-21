# Здесь функции-действия.
# Они выполняют работу: ищут данные, формируют ответ и т.п.
# На вход получают "контекст" (ctx) = словарь с данными о пользователе.

def find_oem_size(ctx: dict) -> dict:
    """
    Подбирает штатный размер шин по машине.
    ctx содержит: car_make, car_model, car_year.
    Здесь пока делаем фейковые данные (заглушку).
    """
    make = ctx.get("car_make", "Unknown")
    model = ctx.get("car_model", "Unknown")
    year = ctx.get("car_year", "????")

    # В реальности тут можно подключить API/БД
    size = "205/55 R16"

    ctx["size_raw"] = size
    return {"text": f"Для {make} {model} {year} подойдёт размер {size}"}

def search_tires(ctx: dict) -> dict:
    """
    Подбирает варианты шин по параметрам.
    ctx содержит: size_raw, season, budget, brand_pref.
    """
    size = ctx.get("size_raw", "?")
    season = ctx.get("season", "?")
    budget = ctx.get("budget", "?")
    brand_pref = ctx.get("brand_pref", "Без разницы")

    # Заглушка: список вариантов
    offers = [
        {"brand": "Michelin", "model": "Primacy 4", "price": 12000},
        {"brand": "Continental", "model": "PremiumContact 6", "price": 11500},
        {"brand": "Nokian", "model": "Hakka Green 3", "price": 9500},
    ]

    ctx["offers"] = offers
    return {"text": f"Нашёл {len(offers)} вариантов для {size} ({season}, {budget}, {brand_pref})"}

def render_offers(ctx: dict) -> dict:
    """
    Форматирует найденные предложения в красивый текст.
    ctx["offers"] должен содержать список словарей с ключами brand/model/price.
    """
    offers = ctx.get("offers", [])
    if not offers:
        return {"text": "К сожалению, ничего не нашлось."}

    # Собираем список строк
    lines = []
    for offer in offers:
        lines.append(f"{offer['brand']} {offer['model']} — {offer['price']} ₽")

    return {"text": "Доступные варианты:\n" + "\n".join(lines)}