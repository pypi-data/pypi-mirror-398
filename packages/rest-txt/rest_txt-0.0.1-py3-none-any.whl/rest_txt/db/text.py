
from datetime import datetime, timezone
import sqlite3

# https://sqlite.org/docs.html

_SQL_INIT = """
CREATE TABLE IF NOT EXISTS entries(
	id TEXT PRIMARY KEY,
	content BLOB,
	lastmod
);
"""
_SQL_COUNT = """
SELECT count(*)
FROM entries
WHERE id = ?
"""
_SQL_CREATE = """
INSERT INTO entries(
	id,
	content,
	lastmod
)
VALUES(?, ?, ?)
"""
_SQL_DELETE = """
DELETE FROM entries
WHERE id = ?
"""
_SQL_INFO = """
SELECT length(content), lastmod
FROM entries
WHERE id = ?
"""
_SQL_READ = """
SELECT content, lastmod
FROM entries
WHERE id = ?
"""
_SQL_UPDATE = """
UPDATE entries
SET content = ?, lastmod = ?
WHERE id = ?
"""


def _dt_now():
	return datetime.now(timezone.utc)


class TextStorage:
	def __init__(self, path: str):
		self._conn = sqlite3.connect(path)

	def _exec(self, sql: str, params: tuple = ()):
		return self._conn.execute(sql, params)

	def close(self):
		self._conn.close()

	def create_entry(self, entry_id: str, content: bytes):
		now = _dt_now()

		self._exec(_SQL_CREATE, (entry_id, content, now.isoformat()))

		return entry_id

	def delete_entry(self, entry_id: str):
		self._exec(_SQL_DELETE, (entry_id,))

	def entry_info(self, entry_id: str):
		cursor = self._exec(_SQL_INFO, (entry_id,))

		rows = list(cursor)
		if len(rows) == 0:
			return None
		else:
			row = rows[0]

			length: int = row[0]
			lastmod: datetime = datetime.fromisoformat(row[1])

			return length, lastmod

	def has_entry(self, entry_id: str):
		cursor = self._exec(_SQL_COUNT, (entry_id,))

		count: int = cursor.fetchone()[0]

		return count == 1

	def read_entry(self, entry_id: str):
		cursor = self._exec(_SQL_READ, (entry_id,))

		rows = list(cursor)
		if len(rows) == 0:
			return None
		else:
			row = rows[0]

			content: bytes = row[0]
			lastmod: datetime = datetime.fromisoformat(row[1])

			return content, lastmod

	def update_entry(self, entry_id: str, content: bytes):
		now = _dt_now()

		self._exec(_SQL_UPDATE, (content, now.isoformat(), entry_id))

	def tx_begin(self):
		self._exec('BEGIN EXCLUSIVE TRANSACTION')

	def tx_commit(self):
		self._exec('COMMIT TRANSACTION')


def _init(txts: TextStorage):
	txts._exec(_SQL_INIT)

