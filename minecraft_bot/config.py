import os
import json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
SHEET_NAME = os.getenv("SHEET_NAME", "MinecraftStateBot")

creds_raw = os.getenv("GOOGLE_CREDS_JSON")
GOOGLE_CREDS = json.loads(creds_raw) if creds_raw else None
