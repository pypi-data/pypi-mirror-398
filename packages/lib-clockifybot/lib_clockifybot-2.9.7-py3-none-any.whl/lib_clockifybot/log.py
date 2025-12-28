import logging
import os

from dotenv import load_dotenv
from telebot import TeleBot

load_dotenv(os.getenv("CLOCKIFY_ENV"))


def add_log(the_error, username, file_path=None):
    log_channel_id = str(os.getenv("LOG_CHANNEL_ID"))
    current_dir = os.path.dirname(os.getenv("CLOCKIFY_LOG_DIR"))
    logging_bot = TeleBot(os.getenv("TOKEN_LOGGING"))
    log_filename = os.path.join(current_dir, f"{username}_logs.log")
    logging.basicConfig(
        filename=log_filename,
        level=logging.ERROR,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.error(the_error)
    logging_bot.send_message(log_channel_id, f"{username} - {the_error}")
    try:
        if file_path:
            with open(file_path, "rb") as file:
                logging_bot.send_document(os.getenv("BACKUP_CHANNEL_ID"), file)
    except Exception as e:
        logging_bot.send_message(log_channel_id, f"Error in sending Backup - {e}")
