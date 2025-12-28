import os
import subprocess
import threading
import time
from datetime import datetime as dt

import pytz
import schedule

from .config import REPORT_USERNAME
from .log import add_log

tehran_tz = pytz.timezone("Asia/Tehran")


def backup_command(backup_file, username):
    db_name = "clockifybot" if username == REPORT_USERNAME else "timetrackerbot"
    return [
        "pg_dump",
        "-h",
        "localhost",
        "-p",
        "5432",
        "-U",
        os.getenv("POSTGRES_USER"),
        db_name,
        "-f",
        backup_file,
    ]


def backup_database(bot):
    os.environ["PGPASSWORD"] = os.getenv("POSTGRES_PASSWORD")
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    timestamp = dt.now(tehran_tz).strftime("%Y%m%d_%H%M%S")
    bot_username = bot.get_me().username
    backup_file = os.path.join(backup_dir, f"{bot_username}_{timestamp}.sql")
    command = backup_command(backup_file, bot_username)
    try:
        subprocess.run(command, check=True)
        txt = f"Backup created at: {backup_file}"
        add_log(txt, bot.get_me().username, backup_file)
    except subprocess.CalledProcessError as e:
        add_log(f"Error during backup: {e}", bot.get_me().username)
    finally:
        if "PGPASSWORD" in os.environ:
            del os.environ["PGPASSWORD"]
        os.remove(backup_file)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


def runner(bot):
    add_log(
        f"Bot Started at {dt.now(tehran_tz).strftime('%Y-%m-%d %H:%M:%S')}",
        bot.get_me().username,
    )
    print("Bot is polling...")
    threading.Thread(target=run_scheduler, daemon=True).start()
    schedule.every(12).hours.do(job_func=backup_database, bot=bot)
    bot.polling()
    add_log(
        f"Bot Stopped at {dt.now(tehran_tz).strftime('%Y-%m-%d %H:%M:%S')}",
        bot.get_me().username,
    )
