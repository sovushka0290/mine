import gspread_asyncio
from google.oauth2.service_account import Credentials
from config import GOOGLE_CREDS, SHEET_NAME

def get_creds():
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    return Credentials.from_service_account_info(GOOGLE_CREDS, scopes=scopes)

agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)


async def get_ws(tab: str):
    agc = await agcm.authorize()
    sh = await agc.open(SHEET_NAME)
    return await sh.worksheet(tab)


# ─── USERS ────────────────────────────────────────────────────────────────────

async def get_or_create_user(telegram_id: int, username: str) -> dict:
    """Найти или создать игрока. Возвращает dict с полями из шапки."""
    ws = await get_ws("users")
    records = await ws.get_all_records()
    for rec in records:
        if str(rec["telegram_id"]) == str(telegram_id):
            return rec
    # Новый игрок
    await ws.append_row([telegram_id, username, "", "player", 0])
    return {"telegram_id": telegram_id, "username": username,
            "nickname": "", "role": "player", "reputation": 0}


async def set_nickname(telegram_id: int, nickname: str):
    ws = await get_ws("users")
    records = await ws.get_all_records()
    for i, rec in enumerate(records, start=2):
        if str(rec["telegram_id"]) == str(telegram_id):
            await ws.update_cell(i, 3, nickname)
            return


async def get_all_users() -> list:
    ws = await get_ws("users")
    return await ws.get_all_records()


async def add_reputation(telegram_id: int, amount: int):
    ws = await get_ws("users")
    records = await ws.get_all_records()
    for i, rec in enumerate(records, start=2):
        if str(rec["telegram_id"]) == str(telegram_id):
            new_rep = int(rec.get("reputation", 0)) + amount
            await ws.update_cell(i, 5, new_rep)
            return


# ─── TASKS ────────────────────────────────────────────────────────────────────

async def get_all_tasks() -> list:
    ws = await get_ws("tasks")
    return await ws.get_all_records()


async def add_task(title: str, description: str, resource: str, quantity: int, deadline: str) -> int:
    """Добавить задачу, вернуть её ID (номер строки - 1)."""
    ws = await get_ws("tasks")
    records = await ws.get_all_records()
    task_id = len(records) + 1
    await ws.append_row([task_id, title, description, resource, quantity, deadline, "active"])
    return task_id


async def delete_task(task_id: int):
    ws = await get_ws("tasks")
    records = await ws.get_all_records()
    for i, rec in enumerate(records, start=2):
        if str(rec.get("id")) == str(task_id):
            await ws.delete_rows(i)
            return


# ─── REPORTS ──────────────────────────────────────────────────────────────────

async def add_report(telegram_id: int, username: str, resource: str, quantity: int, photo_id: str) -> int:
    ws = await get_ws("reports")
    records = await ws.get_all_records()
    report_id = len(records) + 1
    await ws.append_row([report_id, telegram_id, username, resource, quantity, photo_id, "pending"])
    return report_id


async def get_pending_reports() -> list:
    ws = await get_ws("reports")
    records = await ws.get_all_records()
    return [r for r in records if r.get("status") == "pending"]


async def update_report_status(report_id: int, status: str):
    ws = await get_ws("reports")
    records = await ws.get_all_records()
    for i, rec in enumerate(records, start=2):
        if str(rec.get("id")) == str(report_id):
            await ws.update_cell(i, 7, status)
            return rec
    return None


async def get_report_by_id(report_id: int) -> dict | None:
    ws = await get_ws("reports")
    records = await ws.get_all_records()
    for rec in records:
        if str(rec.get("id")) == str(report_id):
            return rec
    return None


# ─── WAREHOUSE ────────────────────────────────────────────────────────────────

async def get_warehouse() -> list:
    ws = await get_ws("warehouse")
    return await ws.get_all_records()


async def add_to_warehouse(resource: str, amount: int):
    ws = await get_ws("warehouse")
    records = await ws.get_all_records()
    for i, rec in enumerate(records, start=2):
        if rec.get("resource_name", "").lower() == resource.lower():
            new_count = int(rec.get("count", 0)) + amount
            await ws.update_cell(i, 2, new_count)
            return
    # Новый ресурс
    await ws.append_row([resource, amount])


# ─── WARNS ────────────────────────────────────────────────────────────────────

async def add_warn(telegram_id: int, username: str, reason: str):
    ws = await get_ws("warns")
    await ws.append_row([telegram_id, username, reason])


async def get_warns(telegram_id: int) -> list:
    ws = await get_ws("warns")
    records = await ws.get_all_records()
    return [r for r in records if str(r.get("telegram_id")) == str(telegram_id)]
