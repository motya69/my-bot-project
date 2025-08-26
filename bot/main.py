import os
from typing import Dict, Any

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from dotenv import load_dotenv
from telebot import types
from bot.dialogs import FLOW
from bot.dialogs.tires.questions import TEXT_T  # ← добавь к импортам
# ⭐ NEW: импорт конкретных валидаторов/действий из твоих модулей
from bot.validators import is_nonempty, is_year, is_number, is_tire_size, is_pcd
from bot.actions import (
    find_oem_size, search_tires, render_tire_offers,
    find_oem_wheels, search_wheels, render_wheels_offers,
)

# ===== Кнопки управления и текст помощи =====
BACK_BTN = "⬅️ Назад"


HELP_TEXT = (
    "👋 Я помогу подобрать шины/диски.\n\n"
    "Команды:\n"
    "• /start — начать заново\n"
    "• /back — шаг назад\n"
    "• /cancel — сбросить диалог\n"
    "• /help — справка\n\n"
    "Подсказки:\n"
    "• Выбирай кнопки под сообщением.\n"
    "• Если вводишь размер шин — используй формат вроде 205/55 R16.\n"
)

# ───────── Конфиг ─────────
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")  # ⭐ NEW (parse_mode="HTML")

bot.set_my_commands([
    types.BotCommand("start", "Перезапуск бота"),
    types.BotCommand("help", "Как пользоваться"),
    types.BotCommand("my_orders", "Мои заказы"),
])

# Включаем системную кнопку «Меню», которая показывает эти команды
# Включаем кнопку «Меню» (системное меню)
bot.set_chat_menu_button(menu_button=types.MenuButtonCommands(type="commands"))

# ───────── Состояние ─────────
STATE: Dict[int, Dict[str, Any]] = {}  # chat_id -> {"node": "...", "ctx": {...}, "history": [...]}  # ⭐ NEW типы

def get_user(chat_id: int) -> Dict[str, Any]:
    if chat_id not in STATE:
        STATE[chat_id] = {"node": "start", "ctx": {}, "history": []}  # ⭐ NEW (history)
    return STATE[chat_id]

def reset_user(chat_id: int) -> None:  # ⭐ NEW
    STATE[chat_id] = {"node": "start", "ctx": {}, "history": []}
ERROR_HINT = "⚠️ Кажется, что-то не так с ответом. Проверь данные и попробуй ещё раз."

def go_back(chat_id: int, reason: str = ERROR_HINT) -> None:
    """
    Откат на предыдущий узел с сообщением об ошибке.
    Если истории нет — просто повторяем текущий узел.
    """

    u = get_user(chat_id)                  # берём состояние
    hist = u.get("history") or []          # история узлов

    bot.send_message(chat_id, reason)      # сообщаем об ошибке

    if hist:                               # если есть куда откатиться
        prev = hist.pop()                  # достаём предыдущий узел
        u["node"] = prev                   # записываем его как текущий
        send_node(chat_id, prev)           # показываем вопрос/кнопки этого узла
    else:                                  # если истории нет
        send_node(chat_id, u.get("node", "start"))  # повторяем текущий шаг
RETRY_HINT = "⚠️ Кажется, что-то не так с ответом. Проверь данные и попробуй ещё раз."

def repeat_node(chat_id: int, reason: str = RETRY_HINT) -> None:
    """
    Показывает сообщение об ошибке и ПОВТОРЯЕТ текущий узел (без отката в history).
    Используем для ошибок пользователя: неверный формат, введён не тот вариант и т.п.
    """
    u = get_user(chat_id)
    bot.send_message(chat_id, reason)
    send_node(chat_id, u.get("node", "start"))
# ───────── UI утилиты ─────────
def make_keyboard(buttons, show_back=True):
    """
    Собирает клавиатуру из кнопок сценария + кнопки управления.
    show_back=False на стартовом шаге (чтобы не было 'Назад').
    """
    # Если вообще нет кнопок и не хотим показывать контролы — убираем клавиатуру
    if not buttons and not show_back:
        return ReplyKeyboardRemove()

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    # Кнопки сценария
    for b in (buttons or []):
        kb.add(KeyboardButton(b))
    # Кнопки управления
    controls = []
    if show_back:
        controls.append(BACK_BTN)
    if controls:
        row = [KeyboardButton(x) for x in controls]
        kb.row(*row)
    return kb

def send_node(chat_id: int, node_key: str) -> None:
    """Отправить текст узла + кнопки сценария и управления."""
    node = FLOW[node_key]
    text = node.get("text", "")
    buttons = node.get("buttons")
    show_back = (node_key != "start")  # на первом шаге «Назад» не показываем
    kb = make_keyboard(buttons, show_back=show_back)
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

ACTIONS = {
    # Шины
    "find_oem_size": find_oem_size,
    "search_tires": search_tires,
    "render_tire_offers": render_tire_offers,

    # Диски
    "find_oem_wheels": find_oem_wheels,
    "search_wheels": search_wheels,
    "render_wheels_offers": render_wheels_offers,
}

def run_action(name: str, chat_id: int, ctx: Dict[str, Any]) -> None:
    fn = ACTIONS.get(name)
    if not fn:
        go_back(chat_id, f"⚠️ Действие '{name}' не найдено. Попробуйте ещё раз.")
        return
    try:
        fn(bot, chat_id, ctx)
    except Exception as e:
        print(f"[ACTION ERROR] {name}: {e}", flush=True)
        go_back(chat_id, "⚠️ Техническая ошибка. Вернул(а) вас на шаг назад.")
# ⭐ NEW: куда сохранять выбор кнопок по узлам
SAVE_BUTTON_TO = {
    # Шины
    "t_ask_season": "season",
    "t_ask_budget": "budget",
    "t_ask_brand_pref": "brand_pref",
    "t_ask_car_make": "car_make",
    "t_ask_car_model_Toyota": "car_model",
    "t_ask_car_model_VW": "car_model",
    "t_ask_car_model_BMW": "car_model",

    # Диски
    "w_ask_diameter": "diameter",
    "w_ask_width": "width",
    "w_ask_pcd": "pcd",
    "w_ask_et": "et",
    "w_ask_dia": "dia",
}

START_BTN = "🟢 Поехали ⚙️"   # добавим константу
def _find_welcome_asset() -> str | None:
    """Ищем существующий не-пустой файл в assets/start.(jpg|jpeg|png). Возвращаем абсолютный путь или None."""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
    for name in ("start.jpg", "start.jpeg", "start.png"):
        p = os.path.join(base, name)
        try:
            if os.path.exists(p) and os.path.isfile(p) and os.path.getsize(p) > 0:
                return p
        except Exception:
            pass
    return None
@bot.message_handler(commands=["start"])
def cmd_start(message):
    reset_user(message.chat.id)

    caption = (
        "<b>Exclusive Wheels 18/ Шины и диски Ижевск</b>\n\n"
        "🔍 Найдём вам отличный вариант!\n"
        "💰 Лучшая цена / качество\n"
        "📦 Только в наличии"
    )

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(START_BTN))

    photo_path = _find_welcome_asset()
    print("[START] resolved asset:", photo_path, flush=True)

    sent = False
    if photo_path:
        try:
            with open(photo_path, "rb") as f:
                bot.send_photo(
                    message.chat.id,
                    photo=f,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb
                )
            sent = True
        except Exception as e:
            print(f"[WARN] send local photo failed: {e}", flush=True)

    if not sent:
        # Надёжный fallback-URL (замени на свой при желании)
        fallback_url = "https://ibb.co/bgBT6mnr"
        try:
            bot.send_photo(
                message.chat.id,
                photo=fallback_url,
                caption=caption,
                parse_mode="HTML",
                reply_markup=kb
            )
            sent = True
        except Exception as e:
            print(f"[ERROR] send url photo failed: {e}", flush=True)

    if not sent:
        # Последний вариант — просто текст
        bot.send_message(message.chat.id, caption, parse_mode="HTML", reply_markup=kb)

    # Ставим пользователя на первый узел сценария
    u = get_user(message.chat.id)
    u["node"] = "start"
# 🔥 обработка нажатия на кнопку "Поехали"
@bot.message_handler(func=lambda msg: msg.text == START_BTN)
def handle_start_btn(message):
    chat_id = message.chat.id
    u = get_user(chat_id)

    # переводим в первый узел сценария
    goto(chat_id, "start")

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

@bot.message_handler(commands=["cancel"])
def cmd_cancel(message):
    reset_user(message.chat.id)       # очистка состояния
    send_node(message.chat.id, "start")  # сразу показываем стартовый узел

@bot.message_handler(commands=["help"])
def cmd_help(message):
    bot.send_message(message.chat.id, HELP_TEXT)

@bot.message_handler(commands=["my_orders"])
def cmd_my_orders(message):
    bot.reply_to(message, "Пока тут пусто 😊 Скоро добавим историю заказов.")
# ───────── Главный обработчик ─────────
@bot.message_handler(content_types=["text"])
def on_text(message):
    chat_id = message.chat.id
    text = (message.text or "").strip()

    # --- Служебные кнопки/команды: ОБРАБАТЫВАЕМ ПЕРВЫМИ ---
    if text == BACK_BTN:
        u = get_user(chat_id)
        hist = u.get("history") or []
        if hist:
            prev = hist.pop()
            u["node"] = prev
            send_node(chat_id, prev)
        else:
            send_node(chat_id, u.get("node", "start"))
        return

    if text.lower() in ("/help", "help"):
        bot.send_message(chat_id, HELP_TEXT)
        send_node(chat_id, get_user(chat_id).get("node", "start"))
        return

    # --- Дальше логика сценария ---
    u = get_user(chat_id)
    node_key = u.get("node", "start")
    node = FLOW.get(node_key, FLOW["start"])

    try:
        # (необязательно, но удобно) — видно, какие ключи у узла
        # print(f"[DEBUG] node={node_key} keys={list(node.keys())}", flush=True)

        # ── 1) КНОПКИ СЦЕНАРИЯ ──
        buttons = node.get("buttons") or []
        mapping = node.get("next_by_button") or {}

        if buttons:
            # ⛑️ страховка: служебные уже обработаны выше
            if text in BACK_BTN:
                return

            if mapping and isinstance(mapping, dict):
                if text in mapping:
                    save_field = SAVE_BUTTON_TO.get(node_key)
                    if save_field \
                        and not (node_key == "ask_car_make" and text == "Другая") \
                        and not (node_key == "t_ask_budget" and text.startswith("📊")):
                            u["ctx"][save_field] = text
                    goto(chat_id, mapping[text])
                    return
                else:
            # Спец-кейс: на шаге бюджета нажали "📊 Сравнение сегментов"
                    if node_key == "t_ask_budget" and text.startswith("📊"):
                # показываем памятку...
                        bot.send_message(chat_id, TEXT_T["budget_compare"])
                # ...и сразу повторяем ТЕКУЩИЙ узел с кнопками бюджета
                        send_node(chat_id, node_key)
                        return

            # обычный случай: ввели что-то не из кнопок
                    repeat_node(chat_id, "⚠️ Пожалуйста, выберите вариант из кнопок ниже.")
                    return
            else:
                # В узле есть buttons, но нет next_by_button → повтор вопроса и предупреждение в лог
                print(f"[WARN] node '{node_key}' has buttons but no next_by_button", flush=True)
                repeat_node(chat_id, "⚠️ Пожалуйста, выберите вариант из кнопок ниже.")
                return

        # ── 2) ТЕКСТОВЫЙ ВВОД ──
        if node.get("expect") == "text":
            validator_name = node.get("validator")
            if validator_name:
                validator = VALIDATORS.get(validator_name)
                if validator and not validator(text):
                    # Плохой ввод пользователя → повторяем текущий узел
                    repeat_node(chat_id, RETRY_HINT)
                    return

            var_name = node.get("var_name")
            if var_name:
                u["ctx"][var_name] = text

            nxt = node.get("next")
            if nxt:
                goto(chat_id, nxt)
                return
            else:
                # Внутренняя ошибка сценария (нет next) → мягкий откат
                go_back(chat_id, "⚠️ Следующий шаг не настроен. Верну вас назад.")
                return

        # ── 3) ЛИНЕЙНЫЙ ПЕРЕХОД ──
        if "next" in node:
            goto(chat_id, node["next"])
            return

        # Ничего не подошло
        repeat_node(chat_id, "⚠️ Я вас не понял. Попробуйте ещё раз.")

    except Exception as e:
        print(f"[HANDLE ERROR] {e}", flush=True)
        go_back(chat_id, ERROR_HINT)
# ───────── Точка запуска ─────────
def start_polling():
    print("🤖 Бот запущен (polling)…")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True, timeout=20)

if __name__ == "__main__":
    start_polling()