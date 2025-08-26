# Общие действия (например, отрисовка карточек).
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def render_cards(bot, chat_id, items, empty_text="К сожалению, ничего не нашлось."):
    """
    Выводит список карточек с кнопкой "Оформить".
    items: [{title:str, subtitle:str, price:float|int|str, stock:int, url:str}]
    """
    if not items:
        bot.send_message(chat_id, empty_text)
        return
    for it in items:
        title = it.get("title", "")
        subtitle = it.get("subtitle", "")
        price = it.get("price", "")
        stock = it.get("stock", "")
        url = it.get("url", "#")

        text = f"🔸 <b>{title}</b>\n{subtitle}\nЦена: {price} • В наличии: {stock}"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Оформить", url=url))
        bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
