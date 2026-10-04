"""SQLite lifecycle and script execution. Query definitions live in sql/*.sql."""
import sqlite3
from pathlib import Path
from common.config import DB_PATH, ROOT

def connection(path: Path = DB_PATH) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db

def init(path: Path = DB_PATH) -> None:
    with connection(path) as db:
        db.executescript((ROOT/'sql/schema.sql').read_text())

def seed(path: Path = DB_PATH) -> None:
    with connection(path) as db:
        if db.execute('SELECT COUNT(*) FROM orders').fetchone()[0]:
            raise ValueError('Database already contains orders; use db reset to replace it')
        db.executescript((ROOT/'sql/seed_data.sql').read_text())

def clear(path: Path = DB_PATH) -> None:
    with connection(path) as db:
        db.execute('DELETE FROM orders')
        db.execute('DELETE FROM products')
        db.execute('DELETE FROM customers')

def drop(path: Path = DB_PATH) -> None:
    path.unlink(missing_ok=True)

def reset(path: Path = DB_PATH) -> None:
    drop(path)
    init(path)
    seed(path)

def reports(path: Path = DB_PATH) -> list[dict]:
    sections = (ROOT/'sql/reports.sql').read_text().split('-- REPORT ')[1:]
    result=[]
    with connection(path) as db:
        for section in sections:
            title, body = section.split('\n',1)
            statements=[s.strip() for s in body.split(';') if s.strip()]
            # Reports i changes schema; allow repeated report runs.
            if title.startswith('i ') and any(row[1]=='loyalty_tier' for row in db.execute('PRAGMA table_info(customers)')):
                statements=statements[1:]
            rows=[]
            for statement in statements:
                # Strip leading expected-output comments from the first statement.
                sql='\n'.join(line for line in statement.splitlines() if not line.lstrip().startswith('--')).strip()
                if sql:
                    cursor=db.execute(sql)
                    if cursor.description:
                        rows=[dict(row) for row in cursor.fetchall()]
            result.append({'title':title, 'rows':rows})
    return result
