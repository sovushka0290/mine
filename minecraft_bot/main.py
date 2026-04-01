import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from handlers import user, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── Веб-заглушка для Render ──────────────────────────────────────────────────

async def health(request):
    return web.Response(text="OK")


async def start_web():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Web server started on port {port}")


# ─── Напоминания о дедлайнах ──────────────────────────────────────────────────

async def deadline_reminder(bot: Bot):
    from datetime import datetime, timedelta
    from database import sheets

    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)

    tasks = await sheets.get_all_tasks()
    users = await sheets.get_all_users()

    for task in tasks:
        raw = task.get("deadline", "")
        try:
            deadline = datetime.strptime(raw, "%d.%m.%Y").date()
        except Exception:
            continue
        if deadline in (today, tomorrow):
            for u in users:
                try:
                    await bot.send_message(
                        int(u["telegram_id"]),
                        f"⏰ *Напоминание!*\nЗадача *{task['title']}* истекает {raw}!\n"
                        f"Не забудь сдать отчёт 📤",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass


# ─── Точка входа ──────────────────────────────────────────────────────────────

async def main():
    await start_web()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
    dp = Dispatcher()

    dp.include_router(admin.router)
    dp.include_router(user.router)

    # Планировщик напоминаний (каждый час)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(deadline_reminder, "interval", hours=1, args=[bot])
    scheduler.start()

    logger.info("🚀 Minecraft State Bot запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
