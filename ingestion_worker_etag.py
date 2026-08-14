#!/usr/bin/env python3
"""
Ingestion worker with per-feed state (ETag / Last-Modified)

Usage:
  python ingestion_worker_etag.py --once

Stores per-feed state in feeds_state.json in the same directory.
"""
import argparse
import json
import time
import hashlib
import sqlite3
import os
from datetime import datetime, timezone

import feedparser
import requests
from dateutil import parser as dateparser

SOURCES_JSON = 'sources_validated.json'
DB_PATH = 'ingestion_sandbox.db'
STATE_PATH = 'feeds_state.json'
USER_AGENT = 'MindfulNewsFeedIngest/1.1 (+https://example.org)'


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_state(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    return {}


def save_state(path, state):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def canonical_id(entry):
    eid = entry.get('id') or entry.get('guid') or entry.get('link')
    if eid:
        return eid
    base = (entry.get('title','') or '') + '|' + (entry.get('link','') or '') + '|' + (entry.get('published','') or '')
    return hashlib.sha256(base.encode('utf-8')).hexdigest()


def content_hash(title, content):
    h = hashlib.sha256()
    h.update((title or '').strip().encode('utf-8'))
    h.update((content or '').strip().encode('utf-8'))
    return h.hexdigest()


def ensure_db(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS sandbox_articles (
        id TEXT PRIMARY KEY,
        source_name TEXT,
        feed_url TEXT,
        title TEXT,
        link TEXT,
        published TEXT,
        summary TEXT,
        content TEXT,
        author TEXT,
        categories TEXT,
        media_urls TEXT,
        fetched_at TEXT,
        etag TEXT,
        last_modified TEXT,
        content_hash TEXT,
        language TEXT,
        needs_review INTEGER DEFAULT 1,
        inserted_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()


def parse_date(entry):
    for key in ('published', 'updated', 'pubDate'):
        if entry.get(key):
            try:
                return dateparser.parse(entry.get(key)).astimezone(timezone.utc).isoformat()
            except Exception:
                pass
    pd = entry.get('published_parsed') or entry.get('updated_parsed')
    if pd:
        try:
            import time as _time
            return datetime.fromtimestamp(_time.mktime(pd), tz=timezone.utc).isoformat()
        except Exception:
            pass
    return None


def detect_language(text):
    try:
        from langdetect import DetectorFactory, detect
        DetectorFactory.seed = 0
        if not text or not text.strip():
            return ''
        lang = detect(text)
        return (lang or '').lower()
    except Exception:
        return ''


def normalize_entry(entry, source):
    e = {}
    e['id'] = canonical_id(entry)
    e['title'] = (entry.get('title') or '').strip()
    e['link'] = entry.get('link') or ''
    e['published'] = parse_date(entry)
    e['summary'] = (entry.get('summary') or entry.get('description') or '')
    content = ''
    if 'content' in entry and entry['content']:
        parts = [c.get('value','') for c in entry['content'] if c.get('value')]
        content = '\n'.join(parts)
    e['content'] = content or e['summary']
    e['author'] = entry.get('author') or entry.get('dc_creator') or ''
    cats = entry.get('tags') or []
    e['categories'] = ','.join([t.get('term','') for t in cats]) if cats else ''
    media = []
    if 'media_content' in entry:
        for m in entry['media_content']:
            url = m.get('url')
            if url:
                media.append(url)
    e['media_urls'] = ','.join(media)
    e['source_name'] = source.get('name')
    e['feed_url'] = source.get('feed')
    # detect language from title and content (prefer longer text)
    sample = (e['content'] or '') + '\n' + (e['title'] or '')
    lang = detect_language(sample)
    e['language'] = lang
    return e


def fetch_feed(session, feed_url, state_entry):
    headers = {'User-Agent': USER_AGENT}
    if state_entry:
        if state_entry.get('etag'):
            headers['If-None-Match'] = state_entry.get('etag')
        if state_entry.get('last_modified'):
            headers['If-Modified-Since'] = state_entry.get('last_modified')
    try:
        r = session.get(feed_url, headers=headers, allow_redirects=True, timeout=20)
    except Exception as ex:
        return None, {'error': str(ex)}
    if r.status_code == 304:
        return 'not_modified', {'http_status': 304}
    if r.status_code != 200:
        return None, {'http_status': r.status_code}
    # parse content
    parsed = feedparser.parse(r.content)
    meta = {
        'http_status': r.status_code,
        'content_type': r.headers.get('Content-Type',''),
        'etag': r.headers.get('ETag',''),
        'last_modified': r.headers.get('Last-Modified',''),
        'entries_count': len(parsed.entries)
    }
    return parsed, meta


def fetch_and_stage(source, conn, session, state):
    feed_url = source.get('feed')
    if not feed_url:
        print('  skip (no feed):', source.get('name'))
        return 0
    state_entry = state.get(feed_url, {})
    result, meta = fetch_feed(session, feed_url, state_entry)
    if result == 'not_modified':
        print(f"  {source.get('name')} -> not modified")
        # update last_checked
        state_entry['last_checked'] = now_iso()
        state[feed_url] = state_entry
        return 0
    if result is None:
        print(f"  {source.get('name')} -> fetch error ({meta.get('http_status') or meta.get('error')})")
        state_entry['last_checked'] = now_iso()
        state_entry['last_error'] = meta.get('error') or meta.get('http_status')
        state[feed_url] = state_entry
        return 0
    parsed = result
    new_count = 0
    for entry in parsed.entries:
        e = normalize_entry(entry, source)
        chash = content_hash(e['title'], e['content'])
        e['content_hash'] = chash
        e['fetched_at'] = now_iso()
        try:
            conn.execute('''INSERT INTO sandbox_articles (id, source_name, feed_url, title, link, published, summary, content, author, categories, media_urls, fetched_at, etag, last_modified, content_hash, language)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                e['id'], e['source_name'], e['feed_url'], e['title'], e['link'], e['published'], e['summary'], e['content'], e['author'], e['categories'], e['media_urls'], e['fetched_at'], meta.get('etag',''), meta.get('last_modified',''), e['content_hash'], e.get('language','')
            ))
            conn.commit()
            new_count += 1
        except sqlite3.IntegrityError:
            pass
    # update state with etag/last_modified
    state_entry['etag'] = meta.get('etag','')
    state_entry['last_modified'] = meta.get('last_modified','')
    state_entry['last_checked'] = now_iso()
    state_entry['last_entries'] = meta.get('entries_count',0)
    state[feed_url] = state_entry
    print(f"  {source.get('name')} -> {new_count} new (entries: {meta.get('entries_count')})")
    return new_count


def load_sources(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--once', action='store_true')
    args = p.parse_args()

    sources = load_sources(SOURCES_JSON)
    conn = sqlite3.connect(DB_PATH)
    ensure_db(conn)
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})

    state = load_state(STATE_PATH)

    total_new = 0
    for s in sources:
        try:
            n = fetch_and_stage(s, conn, session, state)
            total_new += n
            time.sleep(0.6)
        except Exception as ex:
            print('Error processing', s.get('name'), ex)
    save_state(STATE_PATH, state)
    print('Cycle complete — new items:', total_new)

if __name__ == '__main__':
    main()
