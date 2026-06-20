import asyncio
import logging
import threading

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import database as db
from bot import build_bot_app
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=None)
CORS(app)


# ── Dashboard (index.html) ──────────────────────────────────────────────────
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')


# ── API: ambil semua tugas ──────────────────────────────────────────────────
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    rows = db.get_all_tasks()
    tasks = [{'id': r[0], 'user_id': r[1], 'name': r[2], 'deadline': r[3], 'done': bool(r[4])} for r in rows]
    return jsonify(tasks)


# ── API: tambah tugas ───────────────────────────────────────────────────────
@app.route('/api/tasks', methods=['POST'])
def create_task():
    from datetime import datetime
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    deadline = data.get('deadline', '').strip()
    user_id = data.get('user_id', 0)

    if not name or not deadline:
        return jsonify({'error': 'Nama dan deadline wajib diisi'}), 400

    try:
        dl = datetime.strptime(deadline, '%Y-%m-%dT%H:%M')
    except ValueError:
        return jsonify({'error': 'Format deadline salah'}), 400

    if dl <= datetime.now():
        return jsonify({'error': 'Deadline harus di masa depan'}), 400

    task_id = db.add_task(user_id, name, dl)
    return jsonify({'id': task_id, 'message': 'Tugas berhasil ditambahkan'}), 201


# ── API: tandai selesai ─────────────────────────────────────────────────────
@app.route('/api/tasks/<int:task_id>/done', methods=['POST'])
def mark_done(task_id):
    db.mark_done_by_id(task_id)
    return jsonify({'message': 'Tugas ditandai selesai'})


# ── API: hapus tugas ────────────────────────────────────────────────────────
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    db.delete_task_by_id(task_id)
    return jsonify({'message': 'Tugas dihapus'})


# ── Jalankan bot Telegram (polling) di thread terpisah ──────────────────────
def run_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot_app = build_bot_app()
    # stop_signals=None wajib karena ini bukan main thread (signal handler hanya boleh di main thread)
    bot_app.run_polling(stop_signals=None, close_loop=False)


def bootstrap():
    db.init_db()
    start_scheduler()
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    logger.info("Bot thread started")


bootstrap()

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
