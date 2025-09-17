import os
from typing import Dict, Any

import telebot
from telebot import types

from dotenv import load_dotenv
from bot.data.tire_sizes import smart_widths, smart_heights, smart_diameters
from bot.dialogs import FLOW
from bot.dialogs.tires.questions import TEXT_T  # для текста сравнения сегментов
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.data.wheel_smart import (
    smart_wheel_r, smart_wheel_j, smart_wheel_pcd, smart_wheel_et, smart_wheel_dia
)
# ⭐ Валидаторы/экшены
from bot.validators import (
    is_nonempty, is_year, is_number, is_tire_size, is_pcd, is_vin  # FIX: добавили is_vin
)
from bot.actions import (
    find_oem_size, search_tires, render_tire_offers,
    find_oem_wheels, search_wheels, render_wheels_offers,
)
from bot.actions.vin import tires_sizes_from_vin, wheels_params_from_vin

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

UI_MODE = "single"    # поменяй на "ephemeral", чтобы увидеть второй вариант
def _safe_edit_text(chat_id: int, msg_id: int, text: str, reply_markup=None) -> bool:
    """
    Пытаемся обновить и текст, и разметку. Возвращаем True, если получилось.
    Если возникает 'message is not modified', пробуем обновить только разметку.
    """
    try:
        bot.edit_message_text(
            text,
            chat_id,
            msg_id,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
        return True
    except Exception as e:
        # Частый кейс: "Bad Request: message is not modified"
        msg = str(e).lower()
        if "message is not modified" in msg:
            try:
                bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=reply_markup)
                return True
            except Exception:
                return False
        return False

def send_or_edit(chat_id: int, text: str, reply_markup=None) -> None:
    """
    Если «экран» уже существует — редактируем его.
    Если нет или редактирование не удалось — отправляем новое сообщение и запоминаем ID.
    """
    screen_id = _get_screen_msg_id(chat_id)
    if screen_id:
        ok = _safe_edit_text(chat_id, screen_id, text, reply_markup=reply_markup)
        if ok:
            return
        else:
            # если не получилось отредактировать (удалено/устарело/другие причины) — шлём новое
            try:
                m = bot.send_message(
                    chat_id,
                    text,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )
                _set_screen_msg_id(chat_id, m.message_id)
            except Exception:
                # как совсем резерв: ничего не делаем, чтобы не заспамить
                pass
    else:
        # экрана ещё нет — создаём
        m = bot.send_message(
            chat_id,
            text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        _set_screen_msg_id(chat_id, m.message_id)
def _get_screen_msg_id(chat_id: int) -> int | None:
    return get_user(chat_id).get("screen_msg_id")

def _set_screen_msg_id(chat_id: int, msg_id: int | None) -> None:
    get_user(chat_id)["screen_msg_id"] = msg_id

def _remember_bot_msg(chat_id: int, msg_id: int) -> None:
    u = get_user(chat_id)
    lst = u.setdefault("bot_msgs", [])
    lst.append(msg_id)

def _flush_bot_msgs(chat_id: int) -> None:
    u = get_user(chat_id)
    lst = u.get("bot_msgs") or []
    for mid in lst:
        try:
            bot.delete_message(chat_id, mid)
        except Exception:
            pass
    u["bot_msgs"] = []
def send_ephemeral(chat_id: int, text: str, reply_markup=None) -> None:
    """Вариант B: удаляем все прошлые бот-сообщения и шлём новое."""
    _flush_bot_msgs(chat_id)
    m = bot.send_message(
        chat_id,
        text,
        reply_markup=reply_markup,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    _remember_bot_msg(chat_id, m.message_id)
    # для совместимости, тоже запомним как «экран»
    _set_screen_msg_id(chat_id, m.message_id)



def reset_user(chat_id: int) -> None:
    STATE[chat_id] = {"node": "start", "ctx": {}, "history": []}

ERROR_HINT = "⚠️ Кажется, что-то не так с ответом. Проверь данные и попробуй ещё раз."
RETRY_HINT = "⚠️ Кажется, что-то не так с ответом. Проверь данные и попробуй ещё раз."

def repeat_node(chat_id: int, reason: str = "Попробуйте ещё раз.") -> None:
    u = get_user(chat_id)
    node_key = u.get("node", "start")
    send_node(chat_id, node_key, notice=reason)

def go_back(chat_id: int, reason: str = "Возвращаю на предыдущий шаг.") -> None:
    u = get_user(chat_id)
    hist = u.get("history") or []
    if hist:
        prev = hist.pop()
        u["node"] = prev
        send_node(chat_id, prev, notice=reason)
    else:
        send_node(chat_id, u.get("node", "start"), notice=reason)

# ---------- INLINE UI ----------
def _cb_btn(node_key: str, idx: int) -> str:
    return f"btn::{node_key}::{idx}"

def _cb_back() -> str:
    return "btn::back"

def build_inline_kb(node_key: str, buttons: list[str] | None, show_back: bool) -> InlineKeyboardMarkup | None:
    if not buttons and not show_back:
        return None
        # 👉 для умных подборов (шины + диски) — сетка 4 в ряд
    if node_key in SMART_NODES:
        kb = InlineKeyboardMarkup(row_width=4)
        row = []
        for i, b in enumerate(buttons or []):
            row.append(InlineKeyboardButton(text=b, callback_data=_cb_btn(node_key, i)))
            if len(row) == 4:
                kb.row(*row)
                row = []
        if row:  # остаток < 4
            kb.row(*row)
        if show_back:
            kb.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=_cb_back()))
        return kb

    # 👉 дефолтные кнопки — по 3 в ряд
    kb = InlineKeyboardMarkup(row_width=3)
    for i, b in enumerate(buttons or []):
        kb.add(InlineKeyboardButton(text=b, callback_data=_cb_btn(node_key, i)))
    if show_back:
        kb.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=_cb_back()))
    return kb

def send_node(chat_id: int, node_key: str, notice: str | None = None) -> None:
    node = FLOW[node_key]
    text = node.get("text", "") or ""
    buttons = node.get("buttons") or []

    # динамические списки для умного подбора
    if node_key in SMART_NODES:
        dyn = dynamic_buttons(node_key, get_user(chat_id).get("ctx", {}))
        if dyn is not None:
            buttons = dyn

    # покажем предупреждение (ошибку/подсказку) прямо вверху «экрана»
    if notice:
        text = f"❗️ {notice}\n\n{text}"

    show_back = (node_key != "start")
    kb = build_inline_kb(node_key, buttons, show_back)

    if UI_MODE == "single":
        send_or_edit(chat_id, text, reply_markup=kb)
    else:
        send_ephemeral(chat_id, text, reply_markup=kb)



VIN_SMART = {"t_vin_sizes", "w_vin_params"}
TIRES_SMART  = {"t_smart_width", "t_smart_height", "t_smart_diameter"}
WHEELS_SMART = {"w_smart_r", "w_smart_j", "w_smart_pcd", "w_smart_et", "w_smart_dia"}
SMART_NODES = TIRES_SMART | WHEELS_SMART | VIN_SMART

def dynamic_buttons(node_key: str, ctx: Dict[str, Any]):
    if node_key == "t_smart_width":
        return smart_widths()
    if node_key == "t_smart_height":
        w = str(ctx.get("width") or "")
        return smart_heights(w)
    if node_key == "t_smart_diameter":
        w = str(ctx.get("width") or "")
        h = str(ctx.get("height") or "")
        return [f"R{d}" for d in smart_diameters(w, h)] # красиво с "R"
    # ▼▼▼ НОВОЕ: VIN размеры
    if node_key == "t_vin_sizes":
        return ctx.get("size_options") or []
    # ---- ДИСКИ (умный подбор) ----
    if node_key == "w_smart_r":
        return [f"R{r}" for r in smart_wheel_r(ctx)]
    if node_key == "w_smart_j":
        return smart_wheel_j(ctx)
    if node_key == "w_smart_pcd":
        return smart_wheel_pcd(ctx)
    if node_key == "w_smart_et":
        return smart_wheel_et(ctx)
    if node_key == "w_smart_dia":
        return smart_wheel_dia(ctx)
    if node_key == "w_vin_params":
        return ctx.get("wheel_options") or []
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

    "tires_sizes_from_vin": tires_sizes_from_vin,
    "wheels_params_from_vin": wheels_params_from_vin,
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

    # умный подбор дисков
    "w_smart_r": "wheel_r",
    "w_smart_j": "wheel_j",
    "w_smart_pcd": "wheel_pcd",
    "w_smart_et": "wheel_et",
    "w_smart_dia": "wheel_dia",
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
    _set_screen_msg_id(message.chat.id, None)


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
        raw = buttons[idx]
        choice = str(raw)

        # VIN выбор размера
        if node_key == "t_vin_sizes":
            u["ctx"]["size_raw"] = choice
            goto(chat_id, "t_ask_season")   # ← без node_key=
            bot.answer_callback_query(call.id)
            return

    except Exception:
        bot.answer_callback_query(call.id, text="Ошибка выбора")
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
    if not nxt and node_key in TIRES_SMART:
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
    # выбор комплекта по VIN (диски)
    if node_key == "w_vin_params":
        # пример лейбла: "R17 · 7.5J · 5x120 · ET34 · DIA 72.6"
        parts = choice.replace("·", " ").split()
        # Rxx, xxJ, pcd, ETxx, DIA, dia
        try:
            r   = parts[0][1:] if parts[0].startswith("R") else parts[0]
            j   = parts[1][:-1] if parts[1].endswith("J") else parts[1]
            pcd = parts[2]
            et  = parts[3][2:] if parts[3].startswith("ET") else parts[3]
            dia = parts[5] if parts[4].upper() == "DIA" else parts[4]
            u["ctx"].update({
                "wheel_r": r, "wheel_j": j, "wheel_pcd": pcd, "wheel_et": et, "wheel_dia": dia
            })
        except Exception:
            pass
        goto(chat_id, "w_ask_budget")
        bot.answer_callback_query(call.id)
        return
    # ---- Умный подбор дисков ----
    if node_key in {"w_smart_r","w_smart_j","w_smart_pcd","w_smart_et","w_smart_dia"}:
        ch = choice
        if node_key == "w_smart_r":
            u["ctx"]["wheel_r"] = ch[1:] if ch.startswith("R") else ch
            goto(chat_id, "w_smart_j")
        elif node_key == "w_smart_j":
            u["ctx"]["wheel_j"] = ch[:-1] if ch.endswith("J") else ch
            goto(chat_id, "w_smart_pcd")
        elif node_key == "w_smart_pcd":
            u["ctx"]["wheel_pcd"] = ch
            goto(chat_id, "w_smart_et")
        elif node_key == "w_smart_et":
            u["ctx"]["wheel_et"] = ch[2:] if ch.startswith("ET") else ch
            goto(chat_id, "w_smart_dia")
        elif node_key == "w_smart_dia":
            u["ctx"]["wheel_dia"] = ch
            # готовы к поиску: сразу на бюджет
            goto(chat_id, "w_ask_budget")
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
            if node_key == "t_vin":
                # экшен заполнит ctx["size_options"] по введённому VIN
                from bot.actions.vin import tires_sizes_from_vin
                tires_sizes_from_vin(bot, chat_id, u["ctx"])
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
