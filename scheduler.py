import logging
from datetime import datetime, timedelta
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import database as db
from config import TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
        if r.status_code != 200:
            logger.error(f"Failed: {r.text}")
    except Exception as e:
        logger.error(f"Send error: {e}")


def check_reminders():
    now = datetime.now()
    logger.info(f"Checking at {now}")
    for tid, uid, name, dl in db.get_tasks_to_notify('24h'):
        if dl - now <= timedelta(hours=24) and dl > now:
            send_message(uid, f"⏰ *24 Jam:* {name} deadline besok {dl.strftime('%H:%M')}")
            db.mark_notified(tid, '24h')
    for tid, uid, name, dl in db.get_tasks_to_notify('1h'):
        if dl - now <= timedelta(hours=1) and dl > now:
            dt = int((dl - now).total_seconds() // 60)
            send_message(uid, f"⚠️ *1 Jam lagi:* {name} deadline dalam {dt} menit")
            db.mark_notified(tid, '1h')
    for tid, uid, name, dl in db.get_tasks_to_notify('0h'):
        if dl <= now:
            send_message(uid, f"🔔 *DEADLINE!* {name} sudah jatuh tempo jam {dl.strftime('%H:%M')}")
            db.mark_notified(tid, '0h')


_scheduler = None


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(check_reminders, 'interval', seconds=30)
    _scheduler.start()
    logger.info("Scheduler started")
    return _scheduler
