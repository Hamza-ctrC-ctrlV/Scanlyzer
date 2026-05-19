"""
State Management Module

Replaces in-memory dictionaries with a thread-safe/multi-process safe
SQLite backend for tracking background scan progress and results.
This ensures Server-Sent Events (SSE) work correctly across multiple workers.
"""

import sqlite3
import json
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scan_state.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_progress (
                scan_id TEXT PRIMARY KEY,
                user_id TEXT,
                state_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_results (
                scan_id TEXT PRIMARY KEY,
                user_id TEXT,
                result_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

# Initialize DB on import
init_db()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    try:
        yield conn
    finally:
        conn.close()

def set_scan_progress(scan_id: str, user_id: str, progress_dict: dict):
    with get_db() as conn:
        conn.execute(
            '''INSERT INTO scan_progress (scan_id, user_id, state_json, updated_at) 
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(scan_id) DO UPDATE SET 
               state_json=excluded.state_json, 
               updated_at=CURRENT_TIMESTAMP''',
            (scan_id, user_id, json.dumps(progress_dict))
        )
        conn.commit()

def get_scan_progress(scan_id: str):
    with get_db() as conn:
        cursor = conn.execute('SELECT state_json FROM scan_progress WHERE scan_id = ?', (scan_id,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

def set_scan_result(scan_id: str, user_id: str, result_dict: dict):
    with get_db() as conn:
        conn.execute(
            '''INSERT INTO scan_results (scan_id, user_id, result_json) 
               VALUES (?, ?, ?)
               ON CONFLICT(scan_id) DO UPDATE SET 
               result_json=excluded.result_json''',
            (scan_id, user_id, json.dumps(result_dict))
        )
        conn.commit()

def get_scan_result(scan_id: str):
    with get_db() as conn:
        cursor = conn.execute('SELECT result_json, user_id FROM scan_results WHERE scan_id = ?', (scan_id,))
        row = cursor.fetchone()
        if row:
            return {"data": json.loads(row[0]), "user_id": row[1]}
        return None
