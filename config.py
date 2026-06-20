import os

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN belum diset! Tambahkan environment variable BOT_TOKEN di Railway "
        "(Project Settings -> Variables)."
    )

DATABASE_PATH = "reminder.db"
