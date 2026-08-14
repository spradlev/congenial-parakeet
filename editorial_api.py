#!/usr/bin/env python3
"""
Minimal editorial API for Mindful News Feed

Endpoints:
- GET /articles?sandbox=1&limit=50 -> list sandbox articles needing review
- GET /articles/<id> -> article detail
- POST /articles/<id>/approve -> {"reviewer":"name","notes":"..."}
- POST /articles/<id>/reject -> {"reviewer":"name","notes":"..."}
- GET /approved -> list approved articles

Run:
  python3 editorial_api.py

Note: demo only, no auth. Uses ingestion_sandbox.db in same folder.
"""
from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime, timezone
from flask_cors import CORS

DB_PATH = 'ingestion_sandbox.db'
APP_DIR = os.path.dirname(__file__)

app = Flask(__name__, static_folder='.')
CORS(app)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS approved_articles (
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
        approved_by TEXT,
        approved_at TEXT,
        inserted_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id TEXT,
        reviewer TEXT,
        verdict TEXT,
        notes TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()


@app.route('/')
def root():
    return send_from_directory(APP_DIR, 'admin_ui.html')


@app.route('/articles')
def list_articles():
    sandbox = request.args.get('sandbox', '1')
    limit = int(request.args.get('limit', '50'))
    conn = get_conn()
    cur = conn.cursor()
    if sandbox == '1':
        cur.execute('SELECT * FROM sandbox_articles WHERE needs_review=1 ORDER BY inserted_at DESC LIMIT ?', (limit,))
    else:
        cur.execute('SELECT * FROM sandbox_articles ORDER BY inserted_at DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/articles/<article_id>')
def get_article(article_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM sandbox_articles WHERE id = ?', (article_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'not found'}), 404
    return jsonify(dict(row))


def now_iso():
    return datetime.now(timezone.utc).isoformat()


@app.route('/articles/<article_id>/approve', methods=['POST'])
def approve_article(article_id):
    data = request.get_json() or {}
    reviewer = data.get('reviewer', 'unknown')
    notes = data.get('notes', '')
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM sandbox_articles WHERE id = ?', (article_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'error':'not found'}), 404
    rowd = dict(row)
    # insert into approved_articles
    now = now_iso()
    try:
        cur.execute('''INSERT OR REPLACE INTO approved_articles (id, source_name, feed_url, title, link, published, summary, content, author, categories, media_urls, fetched_at, etag, last_modified, content_hash, language, approved_by, approved_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            rowd['id'], rowd['source_name'], rowd['feed_url'], rowd['title'], rowd['link'], rowd['published'], rowd['summary'], rowd['content'], rowd['author'], rowd['categories'], rowd['media_urls'], rowd['fetched_at'], rowd.get('etag'), rowd.get('last_modified'), rowd.get('content_hash'), rowd.get('language',''), reviewer, now
        ))
        # mark as reviewed
        cur.execute('UPDATE sandbox_articles SET needs_review=0 WHERE id = ?', (article_id,))
        cur.execute('INSERT INTO approvals (article_id, reviewer, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?)', (article_id, reviewer, 'approved', notes, now))
        conn.commit()
    except Exception as ex:
        conn.close()
        return jsonify({'error': str(ex)}), 500
    conn.close()
    return jsonify({'status':'approved', 'article_id': article_id})


@app.route('/articles/<article_id>/reject', methods=['POST'])
def reject_article(article_id):
    data = request.get_json() or {}
    reviewer = data.get('reviewer', 'unknown')
    notes = data.get('notes', '')
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM sandbox_articles WHERE id = ?', (article_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'error':'not found'}), 404
    now = now_iso()
    try:
        cur.execute('UPDATE sandbox_articles SET needs_review=0 WHERE id = ?', (article_id,))
        cur.execute('INSERT INTO approvals (article_id, reviewer, verdict, notes, created_at) VALUES (?, ?, ?, ?, ?)', (article_id, reviewer, 'rejected', notes, now))
        conn.commit()
    except Exception as ex:
        conn.close()
        return jsonify({'error': str(ex)}), 500
    conn.close()
    return jsonify({'status':'rejected', 'article_id': article_id})


@app.route('/approved')
def list_approved():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM approved_articles ORDER BY approved_at DESC LIMIT 100')
    rows = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == '__main__':
    ensure_db()
    app.run(host='127.0.0.1', port=5001, debug=False)
