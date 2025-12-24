import sqlite3 as sql

from ..config import database_file


class RepoBase:
    def __init__(self):
        self._database = sql.connect(database_file)
        self._cursor = self._database.cursor()

    def __del__(self):
        self._cursor.close()
        self._database.close()
