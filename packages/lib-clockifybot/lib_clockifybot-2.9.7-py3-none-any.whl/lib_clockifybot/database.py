import psycopg2
from psycopg2 import sql

from .log import add_log


def get_info_in_database(database_url):
    db_url = database_url.rsplit("/", 1)[0] + "/postgres"
    database_name = database_url.split("/")[-1]
    return db_url, database_name


def create_database_if_not_exists(database_url, bot):
    db_url, database_name = get_info_in_database(database_url)
    conn = psycopg2.connect(db_url)
    try:
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [database_name]
            )
            if not cursor.fetchone():
                cursor.execute(
                    sql.SQL("CREATE DATABASE{}").format(sql.Identifier(database_name))
                )
    except psycopg2.Error as e:
        add_log(
            f"An error occurred in create_database_if_not_exists: {e}",
            bot.get_me().username,
        )
    finally:
        conn.close()
