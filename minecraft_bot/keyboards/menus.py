from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📋 Мои задачи"), KeyboardButton(text="📤 Сдать отчёт")],
        [KeyboardButton(text="📦 Склад"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="⚙️ Профиль")],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="🛡️ Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📢 Объявление"), KeyboardButton(text="📋 Задачи")],
        [KeyboardButton(text="👥 Игроки"), KeyboardButton(text="📦 Склад (А)")],
        [KeyboardButton(text="✅ Отчёты"), KeyboardButton(text="◀️ Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def report_decision(report_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"report_accept:{report_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"report_reject:{report_id}"),
        ]
    ])


def task_list_kb(tasks: list) -> InlineKeyboardMarkup:
    buttons = []
    for t in tasks:
        buttons.append([InlineKeyboardButton(
            text=f"🗑 Удалить «{t['title']}»",
            callback_data=f"del_task:{t['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def players_kb(users: list) -> InlineKeyboardMarkup:
    buttons = []
    for u in users:
        nick = u.get("nickname") or u.get("username") or str(u["telegram_id"])
        buttons.append([InlineKeyboardButton(
            text=f"⚠️ Варн → {nick}",
            callback_data=f"warn_player:{u['telegram_id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )
