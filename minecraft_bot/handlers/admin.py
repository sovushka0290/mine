from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from database import sheets
from keyboards.menus import admin_menu, main_menu, cancel_kb, task_list_kb, players_kb
from states.states import CreateTask, WarnPlayer, EditWarehouse

router = Router()


class IsAdmin(Filter):
    async def __call__(self, msg: Message) -> bool:
        return msg.from_user.id == ADMIN_ID


# ─── ПАНЕЛЬ ───────────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "🛡️ Админ-панель")
async def admin_panel(msg: Message):
    await msg.answer("🛡️ Добро пожаловать, Администратор!", reply_markup=admin_menu())


@router.message(IsAdmin(), F.text == "◀️ Назад")
async def back_to_main(msg: Message):
    await msg.answer("Главное меню:", reply_markup=main_menu(is_admin=True))


# ─── ОБЪЯВЛЕНИЕ ───────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "📢 Объявление")
async def announce_start(msg: Message, state: FSMContext):
    await msg.answer("Введи текст объявления:", reply_markup=cancel_kb())
    await state.set_state("announce")


@router.message(IsAdmin(), F.state == "announce")
async def announce_send(msg: Message, state: FSMContext, bot):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_menu())
        return
    users = await sheets.get_all_users()
    sent = 0
    for u in users:
        try:
            await bot.send_message(int(u["telegram_id"]), f"📢 *Объявление:*\n{msg.text}", parse_mode="Markdown")
            sent += 1
        except Exception:
            pass
    await state.clear()
    await msg.answer(f"✅ Объявление отправлено {sent} игрокам.", reply_markup=admin_menu())


# ─── ЗАДАЧИ ───────────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "📋 Задачи")
async def admin_tasks(msg: Message):
    tasks = await sheets.get_all_tasks()
    if not tasks:
        await msg.answer("Задач нет. Создай первую!", reply_markup=admin_menu())
        return
    await msg.answer("Список задач:", reply_markup=task_list_kb(tasks))
    lines = ["📋 *Задачи:*\n"]
    for t in tasks:
        lines.append(f"#{t['id']} *{t['title']}* — {t.get('resource')} × {t.get('quantity')} (до {t.get('deadline')})")
    await msg.answer("\n".join(lines), parse_mode="Markdown")
    await msg.answer("Нажми кнопку выше чтобы удалить задачу, или /create_task для создания новой.")


@router.message(IsAdmin(), F.text == "/create_task")
async def create_task_start(msg: Message, state: FSMContext):
    await msg.answer("📝 Введи название задачи:", reply_markup=cancel_kb())
    await state.set_state(CreateTask.title)


@router.message(IsAdmin(), CreateTask.title)
async def task_title(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_menu())
        return
    await state.update_data(title=msg.text.strip())
    await msg.answer("📝 Описание задачи:")
    await state.set_state(CreateTask.description)


@router.message(IsAdmin(), CreateTask.description)
async def task_desc(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_menu())
        return
    await state.update_data(description=msg.text.strip())
    await msg.answer("📦 Какой ресурс нужно собрать?")
    await state.set_state(CreateTask.resource)


@router.message(IsAdmin(), CreateTask.resource)
async def task_resource(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_menu())
        return
    await state.update_data(resource=msg.text.strip())
    await msg.answer("🔢 Сколько штук нужно?")
    await state.set_state(CreateTask.quantity)


@router.message(IsAdmin(), CreateTask.quantity)
async def task_quantity(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_menu())
        return
    if not msg.text.strip().isdigit():
        await msg.answer("⚠️ Введи число!")
        return
    await state.update_data(quantity=int(msg.text.strip()))
    await msg.answer("🗓 Дедлайн (формат: 25.01.2026):")
    await state.set_state(CreateTask.deadline)


@router.message(IsAdmin(), CreateTask.deadline)
async def task_deadline(msg: Message, state: FSMContext, bot):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_menu())
        return
    data = await state.get_data()
    task_id = await sheets.add_task(
        data["title"], data["description"],
        data["resource"], data["quantity"], msg.text.strip()
    )
    await state.clear()
    await msg.answer(f"✅ Задача *{data['title']}* создана (#{task_id})!", parse_mode="Markdown", reply_markup=admin_menu())

    # Уведомить всех игроков
    users = await sheets.get_all_users()
    for u in users:
        try:
            await bot.send_message(
                int(u["telegram_id"]),
                f"📋 *Новая задача:* {data['title']}\n"
                f"📦 {data['resource']} × {data['quantity']}\n"
                f"🗓 Дедлайн: {msg.text.strip()}",
                parse_mode="Markdown"
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("del_task:"))
async def delete_task(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Нет доступа.", show_alert=True)
        return
    task_id = int(call.data.split(":")[1])
    await sheets.delete_task(task_id)
    await call.answer(f"Задача #{task_id} удалена!")
    await call.message.edit_reply_markup()
    await call.message.answer("✅ Задача удалена.")


# ─── ИГРОКИ / ВАРНЫ ───────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "👥 Игроки")
async def list_players(msg: Message):
    users = await sheets.get_all_users()
    if not users:
        await msg.answer("Игроков пока нет.")
        return
    await msg.answer("👥 Список игроков (нажми чтобы выдать варн):", reply_markup=players_kb(users))


@router.callback_query(F.data.startswith("warn_player:"))
async def warn_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Нет доступа.", show_alert=True)
        return
    tid = int(call.data.split(":")[1])
    await state.update_data(warn_target=tid)
    await call.message.answer("✍️ Введи причину варна:", reply_markup=cancel_kb())
    await state.set_state(WarnPlayer.reason)
    await call.answer()


@router.message(IsAdmin(), WarnPlayer.reason)
async def warn_reason(msg: Message, state: FSMContext, bot):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_menu())
        return
    data = await state.get_data()
    tid = data["warn_target"]

    users = await sheets.get_all_users()
    target = next((u for u in users if str(u["telegram_id"]) == str(tid)), None)
    nick = target.get("nickname") or target.get("username") or str(tid) if target else str(tid)

    await sheets.add_warn(tid, nick, msg.text.strip())
    warns = await sheets.get_warns(tid)
    await state.clear()

    await msg.answer(
        f"⚠️ Варн выдан игроку *{nick}*. Всего варнов: {len(warns)}/3",
        parse_mode="Markdown",
        reply_markup=admin_menu()
    )
    try:
        await bot.send_message(tid, f"⚠️ Тебе выдан варн!\nПричина: {msg.text.strip()}\nВсего варнов: {len(warns)}/3")
    except Exception:
        pass

    if len(warns) >= 3:
        await msg.answer(f"🚨 У игрока *{nick}* 3 варна — рекомендуется кик!", parse_mode="Markdown")


# ─── СКЛАД (АДМИН) ────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "📦 Склад (А)")
async def admin_warehouse(msg: Message, state: FSMContext):
    items = await sheets.get_warehouse()
    lines = ["📦 *Склад:*\n"]
    for item in items:
        lines.append(f"  • {item['resource_name']}: {item['count']}")
    await msg.answer("\n".join(lines) if items else "Склад пуст.", parse_mode="Markdown")
    await msg.answer("Введи /add_resource чтобы добавить ресурс вручную.")


@router.message(IsAdmin(), F.text == "/add_resource")
async def add_res_start(msg: Message, state: FSMContext):
    await msg.answer("📦 Название ресурса:", reply_markup=cancel_kb())
    await state.set_state(EditWarehouse.resource)


@router.message(IsAdmin(), EditWarehouse.resource)
async def add_res_name(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_menu())
        return
    await state.update_data(resource=msg.text.strip())
    await msg.answer("🔢 Количество:")
    await state.set_state(EditWarehouse.quantity)


@router.message(IsAdmin(), EditWarehouse.quantity)
async def add_res_qty(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_menu())
        return
    if not msg.text.strip().lstrip("-").isdigit():
        await msg.answer("⚠️ Введи число!")
        return
    data = await state.get_data()
    await sheets.add_to_warehouse(data["resource"], int(msg.text.strip()))
    await state.clear()
    await msg.answer(f"✅ Склад обновлён: {data['resource']} {msg.text.strip()} шт.", reply_markup=admin_menu())


# ─── ПРОСМОТР ОТЧЁТОВ ─────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "✅ Отчёты")
async def view_reports(msg: Message, bot):
    reports = await sheets.get_pending_reports()
    if not reports:
        await msg.answer("📭 Нет ожидающих отчётов.")
        return
    for r in reports:
        caption = (
            f"📤 *Отчёт #{r['id']}*\n"
            f"👤 {r.get('username', '?')}\n"
            f"📦 {r.get('resource')} × {r.get('quantity')}"
        )
        try:
            from keyboards.menus import report_decision
            await bot.send_photo(msg.chat.id, r["photo_id"], caption=caption,
                                 reply_markup=report_decision(r["id"]), parse_mode="Markdown")
        except Exception:
            await msg.answer(caption, parse_mode="Markdown")
