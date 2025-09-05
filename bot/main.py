import os
from typing import Dict, Any

import telebot
from telebot import types

from dotenv import load_dotenv
from bot.data.tire_sizes import smart_widths, smart_heights, smart_diameters
from bot.dialogs import FLOW
from bot.dialogs.tires.questions import TEXT_T  # для текста сравнения сегментов
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import ReplyKeyboardRemove
# ⭐ Валидаторы/экшены
from bot.validators import (
    is_nonempty, is_year, is_number, is_tire_size, is_pcd, is_vin  # FIX: добавили is_vin
)
from bot.actions import (
    find_oem_size, search_tires, render_tire_offers,
    find_oem_wheels, search_wheels, render_wheels_offers,
)

# ===== Кнопки управления и текст помощи =====
BACK_BTN = "⬅️ Назад"
START_BTN = "🟢 Поехали ⚙️"
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

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# команды и системное меню
bot.set_my_commands([
    types.BotCommand("start", "Перезапуск бота"),
    types.BotCommand("help", "Как пользоваться"),
    types.BotCommand("my_orders", "Мои заказы"),
])
try:
    # у разных версий API разные сигнатуры — подстрахуемся
    try:
        btn = types.MenuButtonCommands(type="commands")
    except TypeError:
        btn = types.MenuButtonCommands("commands")
    bot.set_chat_menu_button(menu_button=btn)
except Exception as e:
    print(f"[WARN] set_chat_menu_button failed: {e}", flush=True)

# ───────── Состояние ─────────
STATE: Dict[int, Dict[str, Any]] = {}  # chat_id -> {"node": "...", "ctx": {...}, "history": [...]}

def get_user(chat_id: int) -> Dict[str, Any]:
    if chat_id not in STATE:
        STATE[chat_id] = {"node": "start", "ctx": {}, "history": []}
    return STATE[chat_id]

def reset_user(chat_id: int) -> None:
    STATE[chat_id] = {"node": "start", "ctx": {}, "history": []}

ERROR_HINT = "⚠️ Кажется, что-то не так с ответом. Проверь данные и попробуй ещё раз."
RETRY_HINT = "⚠️ Кажется, что-то не так с ответом. Проверь данные и попробуй ещё раз."

def go_back(chat_id: int, reason: str = ERROR_HINT) -> None:
    """Откат на предыдущий узел с сообщением об ошибке."""
    u = get_user(chat_id)
    hist = u.get("history") or []
    bot.send_message(chat_id, reason)
    if hist:
        prev = hist.pop()
        u["node"] = prev
        send_node(chat_id, prev)
    else:
        send_node(chat_id, u.get("node", "start"))

def repeat_node(chat_id: int, reason: str = RETRY_HINT) -> None:
    """Показывает сообщение об ошибке и ПОВТОРЯЕТ текущий узел (без отката)."""
    u = get_user(chat_id)
    bot.send_message(chat_id, reason)
    send_node(chat_id, u.get("node", "start"))

# ---------- INLINE UI ----------
def _cb_btn(node_key: str, idx: int) -> str:
    return f"btn::{node_key}::{idx}"

def _cb_back() -> str:
    return "btn::back"

def build_inline_kb(node_key: str, buttons: list[str] | None, show_back: bool) -> InlineKeyboardMarkup | None:
    if not buttons and not show_back:
        return None
    # 👇 для ширины шин — сетка 4xN
    if node_key == "t_smart_width":
        kb = InlineKeyboardMarkup(row_width=4)
        row = []
        for i, b in enumerate(buttons or []):
            row.append(InlineKeyboardButton(text=b, callback_data=_cb_btn(node_key, i)))
            if len(row) == 4:   # как только набралось 4 → новая строка
                kb.row(*row)
                row = []
        if row:   # остаток (меньше 4)
            kb.row(*row)
        if show_back:
            kb.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=_cb_back()))
        return kb

    kb = InlineKeyboardMarkup(row_width=3)
    for i, b in enumerate(buttons or []):
        kb.add(InlineKeyboardButton(text=b, callback_data=_cb_btn(node_key, i)))
    if show_back:
        kb.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=_cb_back()))
    return kb

def send_node(chat_id: int, node_key: str) -> None:
    node = FLOW[node_key]
    text = node.get("text", "")
    buttons = node.get("buttons") or []

    # динамические списки для умного подбора
    if node_key in SMART_NODES:
        dyn = dynamic_buttons(node_key, get_user(chat_id).get("ctx", {}))
        if dyn is not None:
            buttons = dyn

    show_back = (node_key != "start")
    kb = build_inline_kb(node_key, buttons, show_back)
    bot.send_message(chat_id, text, reply_markup=kb)
SMART_NODES = {"t_smart_width", "t_smart_height", "t_smart_diameter"}

def dynamic_buttons(node_key: str, ctx: Dict[str, Any]):
    if node_key == "t_smart_width":
        return smart_widths()
    if node_key == "t_smart_height":
        w = str(ctx.get("width") or "")
        return smart_heights(w)
    if node_key == "t_smart_diameter":
        w = str(ctx.get("width") or "")
        h = str(ctx.get("height") or "")
        return [f"R{d}" for d in smart_diameters(w, h)]  # красиво с "R"
    return None
def goto(chat_id: int, node_key: str) -> None:
    """Переход в узел (с записью истории) + авто-action."""
    u = get_user(chat_id)
    u.setdefault("history", []).append(u.get("node"))
    u["node"] = node_key
    send_node(chat_id, node_key)

    node = FLOW.get(node_key, {})
    action_name = node.get("action")
    if action_name:
        run_action(action_name, chat_id, u["ctx"])

# ───────── Реестр валидаторов/действий ─────────
VALIDATORS = {
    "is_nonempty": is_nonempty,
    "is_year": is_year,
    "is_number": is_number,
    "is_tire_size": is_tire_size,
    "is_pcd": is_pcd,
    "is_vin": is_vin,  # FIX
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

    # Алиас, если в FLOW вдруг стоит 'render_offers'
    "render_offers": render_tire_offers,
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

# Куда сохранять выбор кнопок по узлам
SAVE_BUTTON_TO = {
    "t_ask_season": "season",
    "t_ask_budget": "budget",
    "t_ask_brand": "brand_pref",

    "t_ask_car_make": "car_make",  # кроме «Другая»
    "t_ask_car_model_Toyota": "car_model",
    "t_ask_car_model_VW": "car_model",
    "t_ask_car_model_BMW": "car_model",

    # VIN ветка
    "t_vin_sizes": "size_raw",

    # Умный подбор
    "t_smart_width": "width",
    "t_smart_height": "height",
    "t_smart_diameter": "diameter",

    # Если позже добавишь ветку дисков — ключи ниже пригодятся
    "w_ask_diameter": "diameter",
    "w_ask_width": "width",
    "w_ask_pcd": "pcd",
    "w_ask_et": "et",
    "w_ask_dia": "dia",

    "w_ask_budget": "w_budget",
    "w_ask_brand": "w_brand_pref",
    "w_ask_car_make": "car_make",
    "w_ask_car_model_Toyota": "car_model",
    "w_ask_car_model_VW": "car_model",
    "w_ask_car_model_BMW": "car_model",
}


def _find_welcome_asset() -> str | None:
    """Ищем assets/start.(jpg|jpeg|png). Возвращаем абсолютный путь или None."""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
    for name in ("start.jpg", "start.jpeg", "start.png"):
        p = os.path.join(base, name)
        try:
            if os.path.exists(p) and os.path.isfile(p) and os.path.getsize(p) > 0:
                return p
        except Exception:
            pass
    return None

# --- Стартовый экран с inline-кнопкой "Поехали" ---
@bot.message_handler(commands=["start"])
def cmd_start(message):
    reset_user(message.chat.id)
    # 🔥 ВРЕМЕННО — убираем старую reply-клавиатуру
    bot.send_message(
        message.chat.id,
        "Добро пожаловать! 👋",   # можно любой текст, но не пустой
        reply_markup=types.ReplyKeyboardRemove()
    )
    caption = (
        "<b>Exclusive Wheels 18/ Шины и диски Ижевск</b>\n\n"
        "🔍 Найдём вам отличный вариант!\n"
        "💰 Лучшая цена / качество\n"
        "📦 Только в наличии"
    )

    start_kb = InlineKeyboardMarkup()
    start_kb.add(
        InlineKeyboardButton(text=START_BTN, callback_data="btn::go::0")
    )

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
                    reply_markup=start_kb
                )
            sent = True
        except Exception as e:
            print(f"[WARN] send local photo failed: {e}", flush=True)

    if not sent:
        fallback_url = "https://ibb.co/bgBT6mnr"
        try:
            bot.send_photo(
                message.chat.id,
                photo=fallback_url,
                caption=caption,
                parse_mode="HTML",
                reply_markup=start_kb
            )
            sent = True
        except Exception as e:
            print(f"[ERROR] send url photo failed: {e}", flush=True)

    if not sent:
        bot.send_message(message.chat.id, caption, parse_mode="HTML", reply_markup=start_kb)

    get_user(message.chat.id)["node"] = "start"



def cb_go_start(call):
    chat_id = call.message.chat.id
    # по желанию можно убрать клавиатуру на приветственном сообщении:
    try:
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    except Exception:
        pass
    goto(chat_id, "start")



@bot.message_handler(commands=["back"])
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
    reset_user(message.chat.id)
    send_node(message.chat.id, "start")

@bot.message_handler(commands=["help"])
def cmd_help(message):
    bot.send_message(message.chat.id, HELP_TEXT)

@bot.message_handler(commands=["my_orders"])
def cmd_my_orders(message):
    bot.reply_to(message, "Пока тут пусто 😊 Скоро добавим историю заказов.")

# ───────── Главный обработчик ─────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("btn::"))
def on_button(call):
    chat_id = call.message.chat.id
    data = call.data
    u = get_user(chat_id)

    # стартовая кнопка «Поехали»
    if data.startswith("btn::go"):
        goto(chat_id, "start")
        bot.answer_callback_query(call.id)
        return

    # Назад
    if data == _cb_back():
        hist = u.get("history") or []
        if hist:
            prev = hist.pop()
            u["node"] = prev
            send_node(chat_id, prev)
        else:
            send_node(chat_id, u.get("node", "start"))
        bot.answer_callback_query(call.id)
        return

    # Обычная кнопка: btn::<node_key>::<idx>
    _, node_key, idx_str = data.split("::", 2)
    node = FLOW.get(node_key, {})
    buttons = node.get("buttons") or []

    # динамические списки (умный подбор)
    if node_key in SMART_NODES:
        dyn = dynamic_buttons(node_key, u.get("ctx", {}))
        if dyn is not None:
            buttons = dyn

    try:
        idx = int(idx_str)
        choice = buttons[idx]
    except Exception:
        bot.answer_callback_query(call.id, "Ошибка выбора")
        return

    # сохранить выбор (если маппинг есть)
    save_field = SAVE_BUTTON_TO.get(node_key)
    if save_field and not (node_key == "t_ask_car_make" and choice == "Другая"):
        u["ctx"][save_field] = choice[1:] if node_key == "t_smart_diameter" and choice.startswith("R") else choice

    # спец-кейс: сравнение сегментов на бюджете
    if node_key == "t_ask_budget" and choice.startswith("📊"):
        bot.send_message(chat_id, TEXT_T["budget_compare"], parse_mode="HTML")
        send_node(chat_id, node_key)
        bot.answer_callback_query(call.id)
        return

    # переход по карте
    next_by = node.get("next_by_button") or {}
    nxt = next_by.get(choice)

    # умный подбор — вручную двигаем
    if not nxt and node_key in SMART_NODES:
        if node_key == "t_smart_width":
            u["ctx"]["width"] = choice
            goto(chat_id, "t_smart_height")
        elif node_key == "t_smart_height":
            u["ctx"]["height"] = choice
            goto(chat_id, "t_smart_diameter")
        elif node_key == "t_smart_diameter":
            d = choice[1:] if choice.startswith("R") else choice
            u["ctx"]["diameter"] = d
            w, h = u["ctx"].get("width"), u["ctx"].get("height")
            u["ctx"]["size_raw"] = f"{w}/{h} R{d}"
            goto(chat_id, "t_ask_season")
        bot.answer_callback_query(call.id)
        return

    if nxt:
        goto(chat_id, nxt)
    else:
        repeat_node(chat_id, "⚠️ Кнопка пока никуда не ведёт.")
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=["text"])
def on_text(message):
    chat_id = message.chat.id
    text = (message.text or "").strip()

    # --- Служебные кнопки / команды (первые!) ---
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

    # --- Текущее состояние узла ---
    u = get_user(chat_id)
    node_key = u.get("node", "start")
    node = FLOW.get(node_key, FLOW["start"])

    try:
        # ── 1) УМНЫЙ ПОДБОР (обрабатываем отдельно) ──
        if node_key in {"t_smart_width", "t_smart_height", "t_smart_diameter"}:
            if node_key == "t_smart_width":
                # ожидаем ширину из списка
                if text in smart_widths():
                    u["ctx"]["width"] = text
                    goto(chat_id, "t_smart_height")
                else:
                    repeat_node(chat_id, "⚠️ Выберите ширину из списка.")
                return

            if node_key == "t_smart_height":
                ok = text in smart_heights(str(u["ctx"].get("width", "")))
                if ok:
                    u["ctx"]["height"] = text
                    goto(chat_id, "t_smart_diameter")
                else:
                    repeat_node(chat_id, "⚠️ Выберите профиль из списка.")
                return

            if node_key == "t_smart_diameter":
                d = text[1:] if text.startswith("R") else text
                ok = d in smart_diameters(str(u["ctx"].get("width","")), str(u["ctx"].get("height","")))
                if ok:
                    u["ctx"]["diameter"] = d
                    w = u["ctx"]["width"]; h = u["ctx"]["height"]
                    u["ctx"]["size_raw"] = f"{w}/{h} R{d}"
                    goto(chat_id, "t_ask_season")
                else:
                    repeat_node(chat_id, "⚠️ Выберите диаметр из списка.")
                return


        # ── 3) ТЕКСТОВЫЙ ВВОД ──
        if node.get("expect") == "text":
            validator_name = node.get("validator")
            if validator_name:
                validator = VALIDATORS.get(validator_name)
                if validator and not validator(text):
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
                go_back(chat_id, "⚠️ Следующий шаг не настроен. Верну вас назад.")
                return

        # ── 4) ЛИНЕЙНЫЙ ПЕРЕХОД ──
        if "next" in node:
            goto(chat_id, node["next"])
            return

        # ничего не подошло
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
