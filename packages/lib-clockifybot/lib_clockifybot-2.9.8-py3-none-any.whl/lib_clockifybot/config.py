import os

from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from telebot import types, TeleBot
from telebot.types import InlineKeyboardMarkup as Ikm, InlineKeyboardButton as Ikb

from .log import add_log

load_dotenv(os.getenv("CLOCKIFY_ENV"))
REPORT_USERNAME = (
    None
    if os.getenv("TOKEN_REPORT") is None
    else TeleBot(os.getenv("TOKEN_REPORT")).get_me().username
)
TRACKER_USERNAME = (
    None
    if os.getenv("TOKEN_TRACKER") is None
    else TeleBot(os.getenv("TOKEN_TRACKER")).get_me().username
)
REPORT_TABLE = "user_report"
REQUEST_CHANNEL_ID = os.getenv("REQUESTS_CHANNEL_ID")
DAYS_FOR_HEADERS = ["SA", "SU", "MO", "TU", "WE", "TH"]
days_dict = {
    "SA": "Saturday",
    "SU": "Sunday",
    "MO": "Monday",
    "TU": "Tuesday",
    "WE": "Wednesday",
    "TH": "Thursday",
    "FR": "Friday",
}
day_order = [
    "Saturday",
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
]
PENDING, SELECTED, CONFIRMED_BY, REJECTED_BY = (
    "PENDING",
    "SELECTED",
    "CONFIRMED_BY",
    "REJECTED_BY",
)
HEADER, SELECT, REMOVE, CONFIRM = "header", "select", "remove", "confirm"
WHOLE_DAY_HOURS = "8-9-10-11-12-13-14-15-16-17-18-19-20-21-22"
SHIFT = "shift"
cancel = "/cancel"
threads = {}
ADMIN_ROLE = "original_admin"
SHARED_API_KEY = os.getenv("API_KEY")
true_flag, false_flag = "True", "False"
ZERO, ONE, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT = 0, 1, 2, 3, 4, 5, 6, 7, 8
monthly, pre_month = "monthly", "previous_month"
commands_report = [types.BotCommand(command="/start", description="Start menu")]
commands_tracker = [
    types.BotCommand(command="/start", description="Start menu"),
    types.BotCommand(command="/api", description="⚙️ Configure the API key"),
]
CONFIRM_TEXT = "🟢 Confirm 🟢"
BACK_TEXT = "🔙 Back"
SELECT_SHIFT_TEXT = "📆 Select your Shift hours in week:"
HEADERS_TYPE = "application/json"
mode_dict = {
    "part-time-remote": "Part-time Remote",
    "part-time-leave": "Part-time Absence",
    "full-time-remote": "Full-time Remote",
    "full-time-leave": "Full-time Absence",
}


def telegram_api_exception(bot, func, error):
    username = bot.get_me().username
    if "message is not modified" in str(error):
        add_log(f"Same content and markup in {func}", username)
    else:
        add_log(f"An error occurred in {func}: {error}", username)


def send_cancel_message(message, session, table):
    try:
        if message.text.lower() == cancel:
            user = get_user(message, session, table)
            user.command = None
            session.commit()
            return True
    except SQLAlchemyError as e:
        add_log(f"SQLAlchemyError in send_cancel_message: {e}", get_bot_by_table(table))
    except Exception as e:
        add_log(f"Exception in send_cancel_message: {e}", get_bot_by_table(table))


def change_command_to_none(user, session, bot):
    try:
        user.command = None
        session.commit()
    except SQLAlchemyError as e:
        add_log(
            f"SQLAlchemyError in change_command_to_none: {e}", bot.get_me().username
        )
    except Exception as e:
        add_log(f"Exception in change_command_to_none: {e}", bot.get_me().username)


def get_user(call_or_message, session, table):
    if isinstance(call_or_message, types.Message):
        chat_id = str(call_or_message.chat.id)
        return session.query(table).filter_by(telegram_id=chat_id).first()
    elif isinstance(call_or_message, types.CallbackQuery):
        chat_id = str(call_or_message.message.chat.id)
        return session.query(table).filter_by(telegram_id=chat_id).first()


def get_bot_by_table(table):
    name = table.__tablename__
    if name == REPORT_TABLE:
        return REPORT_USERNAME
    else:
        return TRACKER_USERNAME


def get_bot_by_user(user):
    name = user.__class__.__tablename__
    if name == REPORT_TABLE:
        return REPORT_USERNAME
    else:
        return TRACKER_USERNAME


def hours_to_txt(hours):
    text = ""
    category_list = create_category_list(hours)
    for category in category_list:
        index = category_list.index(category)
        if len(category) > 1 and index == len(category_list) - 1:
            text += f"{category[0]} to {category[-1]}"
        elif len(category) > 1:
            text += f"{category[0]} to {category[-1]} | "
        elif index == len(category_list) - 1:
            text += f"{category[0]}"
        else:
            text += f"{category[0]} | "
    return text


def create_category_list(hours):
    hours_list = sorted([int(hour) for hour in hours.split("-")])
    category_list = []
    for hour in hours_list:
        index = hours_list.index(hour)
        if index == ZERO:
            category_list.append([hour])
        elif hour - hours_list[index - 1] == ONE:
            category_list[-1].append(hour)
        else:
            category_list.append([hour])
    return category_list


def list_of_dicts_to_inline_keyboard(buttons_list):
    markup = Ikm()
    for button_dict in buttons_list:
        for text, data_dict in button_dict.items():
            callback_data = data_dict.get("callback_data")
            if callback_data is None:
                continue
            btn = Ikb(text=text, callback_data=callback_data)
            markup.add(btn)
    return markup


def dict_to_ikm_obj(btns, max_width=4):
    markup = Ikm()
    for rows in btns:
        row = []
        for btn in rows:
            key = btn.keys()
            value = btn.values()
            row.append(
                Ikb(
                    text=next(iter(key)),
                    callback_data=next(iter(value)).get("callback_data"),
                )
            )
            if len(row) == max_width:
                markup.row(*row)
                row = []
        if row:
            markup.row(*row)
    return markup
