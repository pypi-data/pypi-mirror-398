import os
import sqlite3
import time
import glob
import pandas as pd
from urllib.parse import urlparse, urlunparse
from ohmyscrapper.core import config


def get_db_dir():
    db_folder = config.get_dir('db')
    if not os.path.exists(db_folder):
        os.mkdir(db_folder)
    return db_folder


def get_db_path():
    db_file = config.get_db()
    return os.path.join(get_db_dir(),db_file)


def get_db_connection():
    if not os.path.exists(get_db_path()):
        create_tables(sqlite3.connect(get_db_path()))
    return sqlite3.connect(get_db_path())


def use_connection(func):
    def provide_connection(*args, **kwargs):
        global conn
        with get_db_connection() as conn:
            return func(*args, **kwargs)

    return provide_connection


def create_tables(conn):

    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS urls (id INTEGER PRIMARY KEY, url_type STRING, parent_url TEXT, url TEXT UNIQUE, url_destiny TEXT, h1 TEXT, error TEXT, description TEXT, description_links INTEGER DEFAULT 0, json TEXT, json_ai TEXT, ai_processed INTEGER DEFAULT 0, history INTEGER DEFAULT 0, last_touch DATETIME, created_at DATETIME)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS ai_log (id INTEGER PRIMARY KEY, instructions STRING, response STRING, model STRING, prompt_file STRING, prompt_name STRING, created_at DATETIME)"
    )

    c.execute(
        "CREATE TABLE IF NOT EXISTS urls_valid_prefix (id INTEGER PRIMARY KEY, url_prefix TEXT UNIQUE, url_type TEXT)"
    )


def seeds(seeds={}):

    for url_type, url_prefix in seeds.items():
        add_urls_valid_prefix(url_prefix, url_type)

    return True


@use_connection
def add_urls_valid_prefix(url_prefix, url_type):

    df = pd.read_sql_query(
        f"SELECT * FROM urls_valid_prefix WHERE url_prefix = '{url_prefix}'", conn
    )
    if len(df) == 0:
        c = conn.cursor()
        c.execute(
            "INSERT INTO urls_valid_prefix (url_prefix, url_type) VALUES (?, ?)",
            (url_prefix, url_type),
        )
        conn.commit()


@use_connection
def get_urls_valid_prefix_by_type(url_type):
    df = pd.read_sql_query(
        f"SELECT * FROM urls_valid_prefix WHERE url_type = '{url_type}'", conn
    )
    return df


@use_connection
def get_urls_valid_prefix_by_id(id):
    df = pd.read_sql_query(f"SELECT * FROM urls_valid_prefix WHERE id = '{id}'", conn)
    return df


# TODO: pagination required
@use_connection
def get_urls_valid_prefix(limit=0):
    if limit > 0:
        df = pd.read_sql_query(f"SELECT * FROM urls_valid_prefix LIMIT {limit}", conn)
    else:
        df = pd.read_sql_query(f"SELECT * FROM urls_valid_prefix", conn)
    return df


# TODO: pagination required
@use_connection
def get_urls(limit=0):
    if limit > 0:
        df = pd.read_sql_query(
            f"SELECT * FROM urls LIMIT {limit} ORDER BY history ASC", conn
        )
    else:
        df = pd.read_sql_query(f"SELECT * FROM urls ORDER BY history ASC", conn)
    return df


@use_connection
def get_urls_report():
    sql = """
    WITH parent_url AS (
        SELECT parent_url FROM urls WHERE parent_url IS NOT NULL AND parent_url != '' GROUP BY parent_url
    ),
    parents AS (
        SELECT
            u.id,
            u.url,
            u.h1
            FROM urls u
                INNER JOIN parent_url p
                    ON u.url = p.parent_url
    )
    SELECT
        u.id,
        u.url_type,
        u.url,
        COALESCE(u.h1, p.h1) as h1,
        p.url as parent_url,
        p.h1 as parent_h1
        FROM urls u
        LEFT JOIN parents p
            ON u.parent_url = p.url
        WHERE
            u.history = 0
            AND u.url NOT IN (SELECT url FROM parents)
        ORDER BY url_type DESC
    """
    df = pd.read_sql_query(sql, conn)

    return df


@use_connection
def get_url_by_url(url):
    url = clean_url(url)
    df = pd.read_sql_query(f"SELECT * FROM urls WHERE url = '{url}'", conn)

    return df


@use_connection
def get_url_by_id(id):
    df = pd.read_sql_query(f"SELECT * FROM urls WHERE id = '{id}'", conn)

    return df


@use_connection
def get_urls_by_url_type(url_type):
    df = pd.read_sql_query(
        f"SELECT * FROM urls WHERE history = 0 AND url_type = '{url_type}'", conn
    )
    return df


@use_connection
def get_urls_by_url_type_for_ai_process(url_type="linkedin_post", limit=10):
    df = pd.read_sql_query(
        f"SELECT * FROM urls WHERE history = 0 AND url_type = '{url_type}' AND ai_processed = 0 LIMIT {limit}",
        conn,
    )
    return df


@use_connection
def get_url_like_unclassified(like_condition):
    df = pd.read_sql_query(
        f"SELECT * FROM urls WHERE history = 0 AND url LIKE '{like_condition}' AND url_type IS NULL",
        conn,
    )
    return df


@use_connection
def add_url(url, h1=None, parent_url=None):
    url = clean_url(url)
    c = conn.cursor()

    if h1 is not None:
        h1 = h1.strip()

    if parent_url is None:
        parent_url = None

    parent_url = str(parent_url)

    if len(get_url_by_url(url)) == 0:
        c.execute(
            "INSERT INTO urls (url, h1, parent_url, created_at, ai_processed, description_links, history) VALUES (?, ?, ?, ?, 0, 0, 0)",
            (url, h1, parent_url, int(time.time())),
        )
        conn.commit()

    return get_url_by_url(url)


@use_connection
def add_ai_log(instructions, response, model, prompt_file, prompt_name):
    c = conn.cursor()

    c.execute(
        "INSERT INTO ai_log (instructions, response, model, prompt_file, prompt_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (instructions, response, model, prompt_file, prompt_name, int(time.time())),
    )
    conn.commit()


@use_connection
def get_ai_log():
    df = pd.read_sql_query(f"SELECT * FROM ai_log", conn)
    return df


@use_connection
def set_url_destiny(url, destiny):
    url = clean_url(url)
    destiny = clean_url(destiny)
    c = conn.cursor()
    c.execute("UPDATE urls SET url_destiny = ? WHERE url = ?", (destiny, url))
    c.execute(
        "UPDATE urls SET parent_url = ? WHERE url = ?",
        (str(url), destiny),
    )

    conn.commit()


@use_connection
def set_url_h1(url, value):
    value = str(value).strip()
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET h1 = ? WHERE url = ?", (value, url))
    conn.commit()


@use_connection
def set_url_h1_by_id(id, value):
    value = str(value).strip()

    c = conn.cursor()
    c.execute("UPDATE urls SET h1 = ? WHERE id = ?", (value, id))
    conn.commit()


@use_connection
def set_url_ai_processed_by_id(id, json_str):
    value = 1
    value = str(value).strip()
    c = conn.cursor()
    c.execute(
        "UPDATE urls SET ai_processed = ? , json_ai = ? WHERE id = ?",
        (value, json_str, id),
    )
    conn.commit()


@use_connection
def set_url_empty_ai_processed_by_id(id, json_str="empty result"):
    value = 1
    value = str(value).strip()
    c = conn.cursor()
    c.execute(
        "UPDATE urls SET ai_processed = ? , json_ai = ? WHERE ai_processed = 0 AND id = ?",
        (value, json_str, id),
    )
    conn.commit()


@use_connection
def set_url_ai_processed_by_url(url, json_str):
    value = 1
    value = str(value).strip()
    url = clean_url(url)
    c = conn.cursor()
    c.execute(
        "UPDATE urls SET ai_processed = ?, json_ai = ? WHERE url = ?",
        (value, json_str, url),
    )
    conn.commit()


@use_connection
def set_url_description(url, value):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET description = ? WHERE url = ?", (value, url))
    conn.commit()


@use_connection
def set_url_description_links(url, value):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET description_links = ? WHERE url = ?", (value, url))
    conn.commit()


@use_connection
def set_url_json(url, value):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET json = ? WHERE url = ?", (value, url))
    conn.commit()


@use_connection
def set_url_error(url, value):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET error = ? WHERE url = ?", (value, url))
    conn.commit()


@use_connection
def set_url_type_by_id(url_id, url_type):
    c = conn.cursor()
    c.execute(f"UPDATE urls SET url_type = '{url_type}' WHERE id = {url_id}")
    conn.commit()


def clean_url(url):
    if url[0:7] == "http://":
        url = "https://" + url[7:]

    if url[0:8] != "https://":
        url = "https://" + url
    url = url.split("#")[0]
    old_query = urlparse(url).query.split("&")
    new_query = []
    for i in old_query:
        if i[0:4] != "utm_":
            new_query.append(i)

    url = urlunparse(urlparse(url)._replace(query="&".join(new_query))).replace("'", "")
    return url


@use_connection
def get_untouched_urls(
    limit=10, randomize=True, ignore_valid_prefix=False, only_parents=True
):
    where_sql = ""
    if not ignore_valid_prefix:
        where_sql += " AND url_type IS NOT NULL "

    if only_parents:
        where_sql += " AND (parent_url = '' OR parent_url IS NULL) "

    if randomize:
        random_sql = " RANDOM() "
    else:
        random_sql = " created_at DESC "
    sql = f"SELECT * FROM urls WHERE 1 = 1 AND history = 0 {where_sql} AND last_touch IS NULL ORDER BY {random_sql} LIMIT {limit}"
    df = pd.read_sql_query(sql, conn)
    return df


@use_connection
def touch_url(url):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET last_touch = ? WHERE url = ?", (int(time.time()), url))
    conn.commit()


@use_connection
def untouch_url(url):
    url = clean_url(url)
    c = conn.cursor()
    c.execute("UPDATE urls SET last_touch = NULL WHERE url = ?", (url))
    conn.commit()


@use_connection
def untouch_all_urls():
    c = conn.cursor()
    c.execute("UPDATE urls SET last_touch = NULL WHERE history = 0")
    conn.commit()


@use_connection
def set_all_urls_as_history():
    c = conn.cursor()
    c.execute("UPDATE urls SET history = 1")
    conn.commit()


def merge_dbs() -> None:
    production_db_file = get_db_path()
    db_number = -1
    dir = get_db_dir()
    list_of_files = glob.glob(dir + "/*.db")
    list_of_files.remove(production_db_file)
    if len(list_of_files) > 0:
        print("\nAvailable dbs:")
        for index, file in enumerate(list_of_files):
            print(index, ":", file)
        while db_number < 0 or db_number >= len(list_of_files):
            db_number = int(input("Choose the db to merge: "))

        print(list_of_files[db_number])
        source_conn = sqlite3.connect(list_of_files[db_number])
        df = pd.read_sql_query("SELECT * FROM urls", source_conn)
        for index, row in df.iterrows():
            merge_url(
                row["url"],
                f"merged from {list_of_files[db_number]}",
                row["last_touch"],
                row["created_at"],
                row["description"],
                row["json"],
            )


@use_connection
def merge_url(url, h1, last_touch, created_at, description, json):
    url = clean_url(url)
    c = conn.cursor()

    if h1 is not None:
        h1 = h1.strip()

    if len(get_url_by_url(url)) == 0:
        c.execute(
            "INSERT INTO urls (url, h1, last_touch , created_at, history, ai_processed, description_links, description, json) VALUES (?, ?, ?, ?, 1, 0, 0, ? , ?)",
            (url, h1, last_touch, created_at, description, json),
        )
        conn.commit()
