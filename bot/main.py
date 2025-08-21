import os
from typing import Dict, Any

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from dotenv import load_dotenv

from bot.dialogs.flow import FLOW

# ⭐ NEW: импорт конкретных валидаторов/действий из твоих модулей
from bot.validators.validators import is_nonempty, is_year, is_tire_size   # ⭐ NEW
from bot.actions.actions import find_oem_size, search_tires, render_offers  # ⭐ NEW


# ───────── Конфиг ─────────
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")  # ⭐ NEW (parse_mode="HTML")


# ───────── Состояние ─────────
STATE: Dict[int, Dict[str, Any]] = {}  # chat_id -> {"node": "...", "ctx": {...}, "history": [...]}  # ⭐ NEW типы

def get_user(chat_id: int) -> Dict[str, Any]:
    if chat_id not in STATE:
        STATE[chat_id] = {"node": "start", "ctx": {}, "history": []}  # ⭐ NEW (history)
    return STATE[chat_id]

def reset_user(chat_id: int) -> None:  # ⭐ NEW
    STATE[chat_id] = {"node": "start", "ctx": {}, "history": []}


# ───────── UI утилиты ─────────
def make_keyboard(buttons):
    if not buttons:
        return ReplyKeyboardRemove()
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for b in buttons:
        kb.add(KeyboardButton(b))
    return kb

def send_node(chat_id: int, node_key: str) -> None:
    node = FLOW[node_key]
    text = node.get("text", "")
    kb = make_keyboard(node.get("buttons"))
    bot.send_message(chat_id, text, reply_markup=kb)


# ⭐ NEW: авто-выполнение action при переходе в узел
def goto(chat_id: int, node_key: str) -> None:
    u = get_user(chat_id)
    u.setdefault("history", []).append(u.get("node"))  # ⭐ NEW: накапливаем history
    u["node"] = node_key
    send_node(chat_id, node_key)

    node = FLOW.get(node_key, {})
    action_name = node.get("action")
    if action_name:
        run_action(action_name, chat_id, u["ctx"])      # ⭐ NEW


# ───────── Реестр валидаторов/действий ─────────
VALIDATORS = {                      # ⭐ NEW
    "is_nonempty": is_nonempty,
    "is_year": is_year,
    "is_tire_size": is_tire_size,
}

ACTIONS = {                         # ⭐ NEW
    "find_oem_size": lambda bot_, chat_id_, ctx_: find_oem_size(bot_, chat_id_, ctx_),
    "search_tires":  lambda bot_, chat_id_, ctx_: search_tires(bot_, chat_id_, ctx_),
    "render_offers": lambda bot_, chat_id_, ctx_: render_offers(bot_, chat_id_, ctx_),
}

def run_action(name: str, chat_id: int, ctx: Dict[str, Any]) -> None:  # ⭐ NEW
    fn = ACTIONS.get(name)
    if not fn:
        bot.send_message(chat_id, f"⚠️ Действие '{name}' не найдено.")
        return
    try:
        fn(bot, chat_id, ctx)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при выполнении действия '{name}': {e}")


# ⭐ NEW: куда сохранять выбор кнопок по узлам
SAVE_BUTTON_TO = {
    "ask_season": "season",
    "ask_budget": "budget",
    "ask_brand_pref": "brand_pref",
    "ask_car_make": "car_make",  # кроме «Другая» (там текстовый ввод)
    "ask_car_model_Toyota": "car_model",
    "ask_car_model_VW": "car_model",
    "ask_car_model_BMW": "car_model",
}


# ───────── Команды ─────────
@bot.message_handler(commands=["start"])
def cmd_start(message):
    reset_user(message.chat.id)         # ⭐ NEW (чистый старт)
    send_node(message.chat.id, "start")

@bot.message_handler(commands=["back"])  # ⭐ NEW
def cmd_back(message):
    u = get_user(message.chat.id)
    hist = u.get("history") or []
    if hist:
        prev = hist.pop()
        u["node"] = prev
        send_node(message.chat.id, prev)
    else:
        send_node(message.chat.id, u["node"])

@bot.message_handler(commands=["cancel"])  # ⭐ NEW
def cmd_cancel(message):
    reset_user(message.chat.id)
    bot.reply_to(message, "Диалог сброшен. Набери /start, чтобы начать заново.")


# ───────── Главный обработчик ─────────
@bot.message_handler(content_types=["text"])
def on_text(message):
    chat_id = message.chat.id
    text = (message.text or "").strip()
    u = get_user(chat_id)
    node_key = u.get("node", "start")
    node = FLOW.get(node_key, FLOW["start"])

    # ⭐ NEW: переходы по кнопкам + сохранение выбора
    if node.get("buttons") and "next_by_button" in node:
        mapping = node["next_by_button"]
        if text in mapping:
            save_field = SAVE_BUTTON_TO.get(node_key)   # ⭐ NEW
            if save_field and not (node_key == "ask_car_make" and text == "Другая"):
                u["ctx"][save_field] = text             # ⭐ NEW
            goto(chat_id, mapping[text])
            return
        else:
            bot.send_message(chat_id, "Пожалуйста, выберите вариант из кнопок 👇")
            send_node(chat_id, node_key)
            return

    # ⭐ NEW: обработка текстового ввода с валидатором + сохранением var_name
    if node.get("expect") == "text":
        validator_name = node.get("validator")
        if validator_name:
            validator = VALIDATORS.get(validator_name)
            if validator and not validator(text):
                bot.send_message(chat_id, "Похоже, формат не подходит. Попробуйте ещё раз 🙂")
                return

        var_name = node.get("var_name")
        if var_name:
            u["ctx"][var_name] = text

        nxt = node.get("next")
        if nxt:
            goto(chat_id, nxt)
            return
        else:
            bot.send_message(chat_id, "⚠️ Дальнейший шаг не настроен.")
            return

    # Линейный переход, если задан
    if "next" in node:
        goto(chat_id, node["next"])
        return

    bot.send_message(chat_id, "Я вас не понял. Наберите /start, чтобы начать заново.")


# ───────── Точка запуска ─────────
def start_polling():
    print("🤖 Бот запущен (polling)…")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True, timeout=20)

if __name__ == "__main__":
    start_polling()