import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS applicants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, father_name TEXT NOT NULL, dob TEXT NOT NULL,
    address TEXT NOT NULL, email TEXT NOT NULL UNIQUE, phone_no TEXT NOT NULL,
    user_name TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS administrators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS police_officers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS applications (
    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
    applicant_id INTEGER NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    state TEXT NOT NULL,
    document_status TEXT NOT NULL DEFAULT 'pending',
    passport_number TEXT UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(application_id) ON DELETE CASCADE,
    amount INTEGER NOT NULL, status TEXT NOT NULL, reference TEXT);
"""


class Database:
    """Passport Database node (Applicant, Application, Verification Status, Passport details)."""

    def __init__(self, path="passport.db"):
        self.path = path
        conn = self._connect()
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def execute(self, sql, params=()):
        conn = self._connect()
        try:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def query(self, sql, params=()):
        conn = self._connect()
        try:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
        finally:
            conn.close()

    def one(self, sql, params=()):
        rows = self.query(sql, params)
        return rows[0] if rows else None