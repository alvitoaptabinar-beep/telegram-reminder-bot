import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import database as db
from config import TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context):
    await update.message.reply_text(
        "📚 *Tugas Reminder Bot*\n\n"
        "/add Nama Tugas | Tahun-Bulan-Tanggal Waktu\n"
        "Contoh: /add Tugas Kalkulus | 2025-12-01 23:59\n\n"
        "/list - lihat daftar tugas\n"
        "/help - bantuan",
        parse_mode='Markdown'
    )


async def add_task(update: Update, context):
    args = ' '.join(context.args).split('|')
    if len(args) < 2:
        await update.message.reply_text("Format: /add Nama | 2025-12-01 23:59")
        return
    name = args[0].strip()
    try:
        deadline = datetime.strptime(args[1].strip(), '%Y-%m-%d %H:%M')
        if deadline <= datetime.now():
            await update.message.reply_text("Deadline harus masa depan!")
            return
        db.add_task(update.effective_user.id, name, deadline)
        await update.message.reply_text(f"✅ {name} ditambahkan, deadline {deadline.strftime('%d/%m %H:%M')}")
    except ValueError:
        await update.message.reply_text("Format salah: YYYY-MM-DD HH:MM")


async def list_tasks(update: Update, context):
    tasks = db.get_pending_tasks(update.effective_user.id)
    if not tasks:
        await update.message.reply_text("Tidak ada tugas.")
        return
    text = "📋 Daftar tugas:\n"
    keyboard = []
    for tid, name, dl in tasks:
        text += f"- {name} ({dl.strftime('%d/%m %H:%M')})\n"
        keyboard.append([
            InlineKeyboardButton("✅ Selesai", callback_data=f"done_{tid}"),
            InlineKeyboardButton("🗑️ Hapus", callback_data=f"del_{tid}")
        ])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def button_callback(update: Update, context):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = update.effective_user.id
    if data.startswith('done_'):
        tid = int(data.split('_')[1])
        db.mark_done(tid, uid)
        await q.edit_message_text("✅ Selesai")
    elif data.startswith('del_'):
        tid = int(data.split('_')[1])
        db.delete_task(tid, uid)
        await q.edit_message_text("🗑️ Dihapus")


async def help_command(update: Update, context):
    await update.message.reply_text(
        "/add Nama | YYYY-MM-DD HH:MM\n/list\n/help"
    )


def build_bot_app():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_task))
    application.add_handler(CommandHandler("list", list_tasks))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    return application


def main():
    db.init_db()
    application = build_bot_app()
    application.run_polling()


if __name__ == "__main__":
    main()
