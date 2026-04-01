from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from database import sheets
from keyboards.menus import main_menu, cancel_kb, report_decision
from states.states import RegisterNick, SendReport

router = Router()


# ─── /start ───────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    user = await sheets.get_or_create_user(msg.from_user.id, msg.from_user.username or "")
    if not user.get("nickname"):
        await msg.answer("⛏️ Добро пожаловать! Введи свой никнейм в Minecraft:")
        await state.set_state(RegisterNick.waiting_nick)
    else:
        is_admin = msg.from_user.id == ADMIN_ID
        await msg.answer(
            f"👋 Привет, *{user['nickname']}*! Добро пожаловать в Minecraft State Bot.",
            reply_markup=main_menu(is_admin),
            parse_mode="Markdown"
        )


@router.message(RegisterNick.waiting_nick)
async def process_nick(msg: Message, state: FSMContext):
    nick = msg.text.strip()
    await sheets.set_nickname(msg.from_user.id, nick)
    await state.clear()
    is_admin = msg.from_user.id == ADMIN_ID
    await msg.answer(
        f"✅ Никнейм *{nick}* сохранён! Теперь ты в системе.",
        reply_markup=main_menu(is_admin),
        parse_mode="Markdown"
    )


# ─── ПРОФИЛЬ ──────────────────────────────────────────────────────────────────

@router.message(F.text == "⚙️ Профиль")
async def show_profile(msg: Message):
    user = await sheets.get_or_create_user(msg.from_user.id, msg.from_user.username or "")
    warns = await sheets.get_warns(msg.from_user.id)
    text = (
        f"👤 *Профиль*\n"
        f"Ник: `{user.get('nickname') or '—'}`\n"
        f"Роль: {user.get('role', 'player')}\n"
        f"Репутация: ⭐ {user.get('reputation', 0)}\n"
        f"Варны: ⚠️ {len(warns)}/3"
    )
    await msg.answer(text, parse_mode="Markdown")


# ─── ЗАДАЧИ ───────────────────────────────────────────────────────────────────

@router.message(F.text == "📋 Мои задачи")
async def show_tasks(msg: Message):
    tasks = await sheets.get_all_tasks()
    if not tasks:
        await msg.answer("📋 Активных задач нет.")
        return
    lines = ["📋 *Активные задачи:*\n"]
    for t in tasks:
        lines.append(
            f"▸ *{t['title']}*\n"
            f"  📦 {t.get('resource', '?')} × {t.get('quantity', '?')}\n"
            f"  🗓 Дедлайн: {t.get('deadline', '—')}\n"
            f"  {t.get('description', '')}"
        )
    await msg.answer("\n".join(lines), parse_mode="Markdown")


# ─── СКЛАД ────────────────────────────────────────────────────────────────────

@router.message(F.text == "📦 Склад")
async def show_warehouse(msg: Message):
    items = await sheets.get_warehouse()
    if not items:
        await msg.answer("📦 Склад пуст.")
        return
    lines = ["📦 *Склад государства:*\n"]
    for item in items:
        lines.append(f"  • {item['resource_name']}: **{item['count']}**")
    await msg.answer("\n".join(lines), parse_mode="Markdown")


# ─── СТАТИСТИКА ───────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Статистика")
async def show_stats(msg: Message):
    users = await sheets.get_all_users()
    sorted_users = sorted(users, key=lambda u: int(u.get("reputation", 0)), reverse=True)[:10]
    lines = ["📊 *Топ игроков по репутации:*\n"]
    for i, u in enumerate(sorted_users, 1):
        nick = u.get("nickname") or u.get("username") or str(u["telegram_id"])
        lines.append(f"{i}. {nick} — ⭐ {u.get('reputation', 0)}")
    await msg.answer("\n".join(lines), parse_mode="Markdown")


# ─── ОТЧЁТ ────────────────────────────────────────────────────────────────────

@router.message(F.text == "📤 Сдать отчёт")
async def start_report(msg: Message, state: FSMContext):
    await msg.answer("📸 Отправь фото собранных ресурсов:", reply_markup=cancel_kb())
    await state.set_state(SendReport.photo)


@router.message(SendReport.photo, F.photo)
async def report_got_photo(msg: Message, state: FSMContext):
    await state.update_data(photo_id=msg.photo[-1].file_id)
    await msg.answer("📦 Какой ресурс ты собрал? (например: железо, дерево, алмазы)")
    await state.set_state(SendReport.resource)


@router.message(SendReport.resource)
async def report_got_resource(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=main_menu(msg.from_user.id == ADMIN_ID))
        return
    await state.update_data(resource=msg.text.strip())
    await msg.answer("🔢 Сколько штук?")
    await state.set_state(SendReport.quantity)


@router.message(SendReport.quantity)
async def report_got_quantity(msg: Message, state: FSMContext, bot):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=main_menu(msg.from_user.id == ADMIN_ID))
        return
    if not msg.text.strip().isdigit():
        await msg.answer("⚠️ Введи число!")
        return
    data = await state.get_data()
    quantity = int(msg.text.strip())
    user = await sheets.get_or_create_user(msg.from_user.id, msg.from_user.username or "")
    nick = user.get("nickname") or user.get("username") or str(msg.from_user.id)

    report_id = await sheets.add_report(
        msg.from_user.id, nick, data["resource"], quantity, data["photo_id"]
    )

    # Уведомить админа
    caption = (
        f"📤 *Новый отчёт #{report_id}*\n"
        f"👤 Игрок: {nick}\n"
        f"📦 Ресурс: {data['resource']} × {quantity}"
    )
    await bot.send_photo(
        ADMIN_ID,
        data["photo_id"],
        caption=caption,
        reply_markup=report_decision(report_id),
        parse_mode="Markdown"
    )
    await state.clear()
    await msg.answer(
        "✅ Отчёт отправлен на проверку администратору!",
        reply_markup=main_menu(msg.from_user.id == ADMIN_ID)
    )


# ─── CALLBACK: решение по отчёту (может нажать и с телефона через inline) ─────

@router.callback_query(F.data.startswith("report_accept:"))
async def accept_report(call: CallbackQuery, bot):
    report_id = int(call.data.split(":")[1])
    report = await sheets.get_report_by_id(report_id)
    if not report or report.get("status") != "pending":
        await call.answer("Уже обработан.", show_alert=True)
        return
    await sheets.update_report_status(report_id, "accepted")
    await sheets.add_to_warehouse(report["resource"], int(report["quantity"]))
    await sheets.add_reputation(int(report["telegram_id"]), 10)
    await call.message.edit_caption(
        call.message.caption + "\n\n✅ *Принято!* +10 репутации игроку.",
        parse_mode="Markdown"
    )
    # Уведомить игрока
    try:
        await bot.send_message(
            int(report["telegram_id"]),
            f"🎉 Твой отчёт #{report_id} принят! +10 ⭐ репутации."
        )
    except Exception:
        pass
    await call.answer("Принято!")


@router.callback_query(F.data.startswith("report_reject:"))
async def reject_report(call: CallbackQuery, bot):
    report_id = int(call.data.split(":")[1])
    report = await sheets.get_report_by_id(report_id)
    if not report or report.get("status") != "pending":
        await call.answer("Уже обработан.", show_alert=True)
        return
    await sheets.update_report_status(report_id, "rejected")
    await call.message.edit_caption(
        call.message.caption + "\n\n❌ *Отклонено.*",
        parse_mode="Markdown"
    )
    try:
        await bot.send_message(
            int(report["telegram_id"]),
            f"😔 Твой отчёт #{report_id} был отклонён администратором."
        )
    except Exception:
        pass
    await call.answer("Отклонено.")
