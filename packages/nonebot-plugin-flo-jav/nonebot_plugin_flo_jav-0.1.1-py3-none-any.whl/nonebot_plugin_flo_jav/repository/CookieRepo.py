from .RepoBase import RepoBase
from ..model import SourceCookie

import sqlite3 as sql
from nonebot.log import logger


class CookieRepo(RepoBase):
    def __init__(self):
        super().__init__()
        create_table_cmd = """
                           CREATE TABLE IF NOT EXISTS source_cookie
                           (
                               source     text PRIMARY KEY,
                               cookie     text NOT NULL,
                               updated_at text NOT NULL
                           ) \
                           """
        self._cursor.execute(create_table_cmd)
        self._database.commit()

    def get_source_cookie(self, source: str) -> SourceCookie | None:
        self._cursor.execute("""
                             SELECT source, cookie, updated_at
                             FROM source_cookie
                             WHERE source = ?
                             """, (source,))
        result = self._cursor.fetchone()
        return SourceCookie().generate_from_db(result) if result else None

    def create_or_update_source_cookie(self, source_cookie: SourceCookie) -> bool:
        source = source_cookie.get_source()
        cookie = source_cookie.get_cookie()
        updated_at = source_cookie.get_updated_at()
        try:
            self._cursor.execute("""
                                 select source, cookie, updated_at
                                 from source_cookie
                                 where source = ?
                                 """, (source,))
            result = self._cursor.fetchone()
            if result is None:
                self._cursor.execute("""
                                     insert into source_cookie (source, cookie, updated_at)
                                     values (?, ?, ?)
                                     """, (source, cookie, updated_at))
            else:
                self._cursor.execute("""
                                     update source_cookie
                                     set cookie     = ?,
                                         updated_at = ?
                                     where source = ?
                                     """, (cookie, updated_at, source))
            self._database.commit()
        except sql.OperationalError as e:
            logger.error(f"Error in create_or_update_source_cookie: {e}")
            return False
        return True


cookie_repo = CookieRepo()
