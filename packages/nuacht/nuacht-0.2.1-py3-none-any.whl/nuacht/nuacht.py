import logging
import sqlite3
import time as tm
from dataclasses import dataclass, asdict
from pathlib import Path
from sqlite3 import Cursor
from typing import Generator

import feedparser
from feedparser import FeedParserDict

import yaml

config_dir = Path('~/.nuacht').expanduser()
config_dir.mkdir(parents=True, exist_ok=True)
log_file = Path(config_dir, 'out.log')
db_file = Path(config_dir, 'entries.db')
feeds_file = Path(config_dir, 'feeds.yaml')
categories_file = Path(config_dir, 'category.map')


@dataclass
class Entry:
    source: str
    url: str
    title: str
    summary: str
    thumbnail: str
    time: int
    tags: str
    categories: str

    def __str__(self) -> str:
        return f'{self.url=} {self.title=} {self.summary=} {self.thumbnail=} {self.time=}'

    def __bool__(self) -> bool:
        return all([self.title, self.url, self.time])

    def err(self) -> str:
        errors = ''
        invalid = [k for k, v in vars(self).items() if not v]
        conj = 'are' if len(invalid) > 1 else 'is'

        while invalid:
            invalid_attr = invalid.pop(0)
            errors += invalid_attr

            if invalid:
                errors += ', '

        return f'{errors} {conj} invalid' if errors else 'No errors'


def set_up_logging(level: int) -> None:
    logging.basicConfig(
        filename=log_file,
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def feeds_iter() -> Generator[tuple[str, str, FeedParserDict], None, None]:
    if not feeds_file.exists():
        logging.error(f'{str(feeds_file)} not found.')
        return

    with open(feeds_file, 'r', encoding='utf-8') as f:
        feeds: dict = yaml.safe_load(f)

    if 'sources' not in feeds:
        logging.error(f'No sources listed in {str(feeds_file)}.')
        return

    logging.info('Iterating feeds.')

    sources = feeds['sources']

    for source_id, source_feeds in sources.items():
        try:
            for key in ['name', 'feeds']:
                if key not in source_feeds:
                    logging.error(f"'{key}' field absent in {str(feeds_file)}:{source_id}")
                    raise KeyError
        except KeyError:
            continue

        name: str = source_feeds['name']
        feeds: list = source_feeds['feeds']

        for feed in feeds:
            try:
                for key in ['id', 'url']:
                    if key not in feed:
                        logging.error(f"'{key}' field absent in {str(feeds_file)}:{source_id}:{name}")
                        raise KeyError
            except KeyError:
                continue

            _id = feed['id']
            url = feed['url']

            logging.info(f'Parsing "{url}".')

            yield name, url, feedparser.parse(url)


def is_feed_valid(source, url: str, feed: FeedParserDict) -> bool:
    logging.info(f'Validating {source}:{url}.')

    if all(['bozo' in feed, feed.bozo]):
        logging.error(f'Bozo in {source}:{url} [{type(feed.bozo_exception).__name__}] {feed.bozo_exception}.')
        return False
    elif any(['entries' not in feed, not len(feed.entries)]):
        logging.error(f'No entries in {source}:{url}.')
        return False
    else:
        return True


def parse_url(entry: FeedParserDict) -> str:
    return entry.link if 'link' in entry else ''


def parse_title(entry: FeedParserDict) -> str:
    return entry.title if 'title' in entry else ''


def parse_summary(entry: FeedParserDict) -> str:
    return entry.summary if 'summary' in entry else ''


def get_max_thumbnail_size(content: list[dict]) -> str:
    return max(content, key=lambda c: int(c['width']))['url']


def parse_thumbnail(entry: FeedParserDict) -> str:
    if 'media_thumbnail' in entry:
        return get_max_thumbnail_size(entry.media_thumbnail)
    elif 'media_content' in entry:
        return get_max_thumbnail_size(entry.media_content)
    else:
        return ''


def parse_published(entry: FeedParserDict) -> int:
    return int(tm.mktime(entry.published_parsed)) if 'published_parsed' in entry else -1


def parse_tags(entry: FeedParserDict) -> str:
    return ','.join(list(map(lambda t: t.term, entry.tags))) if 'tags' in entry else ''


def parse_categories(tags: str, funnel: dict):
    tags = tags.split(',')
    categories = []

    for tag in tags:
        categories.append(funnel.get(tag.lower(), ''))

    return ','.join(categories)


def parse_entry(source: str, entry: FeedParserDict, funnel: dict) -> Entry:
    url = parse_url(entry)
    title = parse_title(entry)
    summary = parse_summary(entry)
    thumbnail = parse_thumbnail(entry)
    time = parse_published(entry)
    tags = parse_tags(entry)
    categories = parse_categories(tags, funnel)
    
    return Entry(
        source,
        url,
        title,
        summary,
        thumbnail,
        time,
        tags,
        categories
    )


def entries_iter(source: str, feed: FeedParserDict, funnel: dict) -> Generator[Entry, None, None]:
    logging.info('Iterating entries.')

    for entry in feed.entries:
        yield parse_entry(source, entry, funnel)


def store_entry_in_database(entry: Entry, cur: Cursor) -> None:
    logging.info(f'Inserting {entry.title} into database.')

    kvs = {k: v for k, v in asdict(entry).items() if v}
    query = f'INSERT OR IGNORE INTO entries ({",".join(kvs.keys())}) VALUES ({",".join(["?"] * len(kvs))})'
    values = tuple(kvs.values())

    cur.execute(query, values)


def delete_older_entries(cur: Cursor, duration: int, verbose: bool) -> None:
    if duration < 0:
        logging.info('Not deleting entries.')
        return

    logging.info(f'Deleting entries older than {duration=}.')

    if verbose:
        cur.execute(f"""SELECT * FROM entries WHERE time < strftime('%s', 'now') - {duration}""")
        rows = cur.fetchall()

        logging.info('Removing entries: ' if rows else 'No entries to remove.')

        for row in rows:
            logging.info(row)

    cur.execute(f"""
        DELETE FROM entries WHERE time < strftime('%s', 'now') - {duration}
    """)


def try_create_table(cur: Cursor) -> None:
    logging.info('Creating table if one does not exist.')

    cur.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            summary TEXT DEFAULT '',
            thumbnail TEXT DEFAULT '',
            time INTEGER NOT NULL,
            tags TEXT DEFAULT '',
            categories TEXT DEFAULT 'Misc.'
        )
    """)


def set_up_category_map() -> dict:
    if not categories_file.exists():
        logging.error(f'{str(categories_file)} not found.')
        return {}

    with open(categories_file, 'r', encoding='utf-8') as f:
        lines = [ln for ln in f.read().split('\n') if ln]

    result = {}

    for line in lines:
        segments = [s.strip() for s in line.split('>>')]
        segments = [s.lower() for s in segments if s]

        if len(segments) != 2:
            logging.error(f'"{line}" does not follow [TAG] >> [CATEGORY] schema.')
            return {}

        tag, category = segments
        result[tag] = category.title()

    return result


def insert_into_database(duration: int = -1, verbose: bool = False) -> None:
    """Duration as a UNIX timestamp"""
    set_up_logging(logging.INFO if verbose else logging.WARN)

    logging.info('Running nuacht.')
    logging.info(f'Opening connection to {db_file}.')

    try:
        conn = sqlite3.connect(db_file)
        conn.execute('PRAGMA foreign_keys = ON')
    except sqlite3.Error as e:
        logging.exception(e)
        return

    funnel = set_up_category_map()
    cur = conn.cursor()

    try_create_table(cur)

    try:
        for source, url, feed in feeds_iter():
            if not is_feed_valid(source, url, feed):
                continue

            for entry in entries_iter(source, feed, funnel):
                if not entry:
                    logging.error(f'{url}: {entry.err()}')
                    continue

                store_entry_in_database(entry, cur)

            logging.info(f'Committing "{url}" insertions.')
            conn.commit()
    except Exception as e:
        logging.exception(e)
        return

    try:
        delete_older_entries(cur, duration, verbose)
    except Exception as e:
        logging.exception(e)
    else:
        logging.info(f'Committing removals.')
        conn.commit()

        logging.info('Closing connection and exiting.')
        conn.close()
