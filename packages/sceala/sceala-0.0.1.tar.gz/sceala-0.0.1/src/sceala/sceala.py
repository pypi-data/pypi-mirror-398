import sqlite3
from pathlib import Path
from typing import Generator
import requests
from requests import RequestException
from time import sleep
from random import uniform as random
from bs4 import BeautifulSoup
import tldextract
import logging
from sqlite3 import Error as Sqlite3Error

config_dir = Path('~/.nuacht').expanduser()
config_dir.mkdir(parents=True, exist_ok=True)
log_file = Path(config_dir, 'out.log')
db_file = Path(config_dir, 'entries.db')
deny_list: set[str] = set()


def set_up_logging(level: int) -> None:
    logging.basicConfig(
        filename=log_file,
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def create_table(cur) -> None:
    cur.execute("""CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY,
        entry_id INTEGER NOT NULL UNIQUE,
        url TEXT NOT NULL UNIQUE,
        text TEXT NOT NULL,
        FOREIGN KEY (entry_id)
            REFERENCES entries(id)
            ON DELETE CASCADE 
    )""")


def get_query(src: str | None) -> str:
    if not src:
        return f"""
            SELECT id, url FROM entries e WHERE NOT EXISTS (SELECT 1 FROM stories s WHERE e.url = s.url) LIMIT ?
        """
    else:
        return f"""
            SELECT id, url FROM entries WHERE NOT EXISTS (SELECT 1 FROM entries WHERE url = ?)
        """


def get_query_result(cur, query: str, src: str | None, limit: int) -> Generator[str, None, None]:
    """
    Returns ROWID and URL from ENTRIES table. ROWID and URL are required for the STORIES table.
    """

    arg = (src if src else limit,)
    cur.execute(query, arg)

    for url in cur.fetchall():
        yield url


def delayed_request(url: str, domain: str) -> bytes:
    delay = random(1.0, 5.0)
    sleep(delay)

    try:
        response = requests.get(url)

        if response.status_code == 403:
            deny_list.add(domain)

        response.raise_for_status()
    except RequestException as err:
        print(err)
        raise
    else:
        return response.content


def get_domain_content(soup, domain: str) -> list[str]:
    if domain == 'rte.ie':
        return [p.get_text() for p in soup.select('#main .article-body p:not([data-embed])')]
    else:
        raise NotImplementedError(f'Domain parsing not implemented for {domain}.')


def parse_content(content: bytes, domain: str) -> str:
    soup = BeautifulSoup(content, 'html.parser')
    res = get_domain_content(soup, domain)

    return '\n'.join(res)


def get_domain(url: str) -> str:
    er = tldextract.extract(url)

    return f'{er.domain}.{er.suffix}'


def store_text(conn, cur, entry_id: int, url: str, text: str) -> None:
    cur.execute("""
        INSERT INTO stories (entry_id, url, text) VALUES (?, ?, ?)
    """, (entry_id, url, text))

    conn.commit()


def get_stories(src: str = None, limit: int = 30) -> None:
    set_up_logging(logging.WARN)

    try:
        conn = sqlite3.connect(db_file)
        conn.execute('PRAGMA foreign_keys = ON')
        cur = conn.cursor()

        create_table(cur)
    except Sqlite3Error as err:
        logging.error(err)
        return

    query: str = get_query(src)

    for entry_id, url in get_query_result(cur, query, src, limit):
        domain = get_domain(url)

        if domain in deny_list:
            continue

        try:
            content = delayed_request(url, domain)
            content = parse_content(content, domain)
        except (NotImplementedError, RequestException) as err:
            logging.error(err)
            continue

        try:
            store_text(conn, cur, entry_id, url, content)
        except sqlite3.IntegrityError as err:
            logging.error(err)
            continue

    conn.close()
