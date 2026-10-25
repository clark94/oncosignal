import json
import sqlite3
from contextlib import contextmanager
from .models import Record, now, digest

SCHEMA = '''
CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY, source TEXT NOT NULL, source_id TEXT NOT NULL,
 kind TEXT NOT NULL, demo INTEGER NOT NULL, review TEXT NOT NULL, hash TEXT NOT NULL, body TEXT NOT NULL,
 UNIQUE(source,source_id));
CREATE TABLE IF NOT EXISTS versions(id INTEGER PRIMARY KEY, record_id TEXT NOT NULL, hash TEXT NOT NULL,
 body TEXT NOT NULL, captured_at TEXT NOT NULL, UNIQUE(record_id,hash));
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, at TEXT NOT NULL, event TEXT NOT NULL, body TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS snapshots(hash TEXT PRIMARY KEY, source TEXT NOT NULL, body TEXT NOT NULL, at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS vectors(record_id TEXT NOT NULL, content_hash TEXT NOT NULL, model TEXT NOT NULL,
 vector TEXT NOT NULL, PRIMARY KEY(record_id,model));
CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY,record_id TEXT NOT NULL,hash TEXT NOT NULL,
 decision TEXT NOT NULL,actor TEXT NOT NULL,note TEXT NOT NULL,at TEXT NOT NULL);
'''

class Store:
    def __init__(self, workspace):
        self.workspace = workspace
        workspace.mkdir(parents=True, exist_ok=True)
        self.path = workspace / 'oncosignal.sqlite'
        with self.connect() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def records(self, include_rejected=False):
        with self.connect() as db:
            rows = db.execute('SELECT body FROM records ORDER BY id').fetchall()
        records = [Record.model_validate_json(r['body']) for r in rows]
        return records if include_rejected else [r for r in records if r.review != 'rejected']

    def get(self, record_id):
        with self.connect() as db:
            row = db.execute('SELECT body FROM records WHERE id=?', (record_id,)).fetchone()
        return Record.model_validate_json(row['body']) if row else None

    def upsert(self, record):
        with self.connect() as db:
            old = db.execute('SELECT hash,review FROM records WHERE id=?', (record.id,)).fetchone()
            state = 'inserted' if not old else ('unchanged' if old['hash'] == record.content_hash else 'updated')
            # Toute modification scientifique invalide la validation éditoriale.
            record = record.model_copy(update={'review': old['review'] if old and state == 'unchanged' else 'pending'})
            db.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET source=excluded.source,source_id=excluded.source_id,kind=excluded.kind,demo=excluded.demo,review=excluded.review,hash=excluded.hash,body=excluded.body',
                       (record.id,record.source,record.source_id,record.kind,int(record.demo),record.review,record.content_hash,record.model_dump_json()))
            db.execute('INSERT OR IGNORE INTO versions(record_id,hash,body,captured_at) VALUES(?,?,?,?)', (record.id,record.content_hash,record.model_dump_json(),now()))
            if state != 'unchanged':
                db.execute('INSERT INTO audit(at,event,body) VALUES(?,?,?)',(now(),state,json.dumps({'record_id':record.id,'hash':record.content_hash})))
        return state

    def snapshot(self, source, payload):
        h = digest(payload)
        with self.connect() as db:
            db.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?,?,?)',(h,source,json.dumps(payload,ensure_ascii=False),now()))
        return h

    def log(self, event, payload):
        with self.connect() as db:
            db.execute('INSERT INTO audit(at,event,body) VALUES(?,?,?)',(now(),event,json.dumps(payload,ensure_ascii=False)))

    def review(self, record_id, decision, actor, note, expected_hash):
        # Vérification de version et mise à jour dans une seule transaction.
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT hash,body FROM records WHERE id=?',(record_id,)).fetchone()
            if not row: raise KeyError(record_id)
            if row['hash'] != expected_hash: raise ValueError('La source a changé : rechargez la fiche avant validation.')
            record=Record.model_validate_json(row['body']).model_copy(update={'review':decision})
            db.execute('UPDATE records SET review=?,body=? WHERE id=?',(decision,record.model_dump_json(),record_id))
            db.execute('INSERT INTO reviews(record_id,hash,decision,actor,note,at) VALUES(?,?,?,?,?,?)',(record_id,expected_hash,decision,actor,note,now()))
        return record

    def audit(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 100')]
