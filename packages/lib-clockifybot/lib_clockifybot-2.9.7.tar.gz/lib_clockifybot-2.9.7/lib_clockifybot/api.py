import requests
from requests import RequestException
from sqlalchemy.exc import SQLAlchemyError

from .config import get_user, get_bot_by_table, send_cancel_message
from .log import add_log


def add_api_key(message, session, table):
    try:
        url = "https://api.clockify.me/api/v1/user"
        response = requests.get(url, headers={"X-Api-Key": message.text})
        if response.ok:
            clockify_id = response.json()["id"]
            user = get_user(message, session, table)
            user.api_key = message.text
            user.clockify_id = clockify_id
            session.commit()
            return True
    except RequestException as e:
        add_log(f"RequestException in add_api_key: {e}", get_bot_by_table(table))
    except SQLAlchemyError as e:
        add_log(f"SQLAlchemyError in add_api_key: {e}", get_bot_by_table(table))
    except UnicodeEncodeError:
        pass
    except Exception as e:
        add_log(f"Exception in add_api_key: {e}", get_bot_by_table(table))


def add_users_api_key(message, session, table):
    try:
        if add_api_key(message, session, table):
            return True
    except ValueError as e:
        add_log(
            f"JSON decoding error in check_users_api_key: {e}", get_bot_by_table(table)
        )
    except KeyError as e:
        add_log(
            f"A command received instead of api key in check_users_api_key: {e}",
            get_bot_by_table(table),
        )
    except Exception as e:
        add_log(f"Exception in check_users_api_key: {e}", get_bot_by_table(table))


def check_users_api_key(message, session, table):
    if send_cancel_message(message, session, table):
        return
    elif add_users_api_key(message, session, table):
        return True
    else:
        return False
