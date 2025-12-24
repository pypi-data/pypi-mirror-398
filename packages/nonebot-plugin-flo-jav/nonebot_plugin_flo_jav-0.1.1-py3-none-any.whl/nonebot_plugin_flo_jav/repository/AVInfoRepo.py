import sqlite3 as sql

from typing import Optional

from nonebot.log import logger

from ..repository import RepoBase
from ..model import AVInfo


class AVInfoRepo(RepoBase):
    def __init__(self):
        super().__init__()
        create_table_cmd = """
                           create table if not exists AVInfo
                           (
                               avid
                               text
                               not
                               null,
                               title
                               text
                               not
                               null,
                               source
                               text
                               not
                               null,
                               release_date
                               text,
                               duration
                               text,
                               producer
                               text,
                               publisher
                               text,
                               series
                               text,
                               category
                               text,
                               actors
                               text,
                               image_url
                               text,
                               primary
                               key
                           (
                               avid,
                               source
                           )
                               )
                           """
        self._cursor.execute(create_table_cmd)
        self._database.commit()

    def get_from_source(self, avid: str, source: Optional[str] = None) -> Optional[AVInfo]:
        if source is None:
            self._cursor.execute("""
                                 select avid,
                                        title,
                                        source,
                                        release_date,
                                        duration,
                                        producer,
                                        publisher,
                                        series,
                                        category,
                                        actors,
                                        image_url
                                 from AVInfo
                                 where avid = ?
                                 """, (avid,))
        else:
            self._cursor.execute("""
                                 select avid,
                                        title,
                                        source,
                                        release_date,
                                        duration,
                                        producer,
                                        publisher,
                                        series,
                                        category,
                                        actors,
                                        image_url
                                 from AVInfo
                                 where avid = ?
                                   and source = ?
                                 """, (avid, source))

        result = self._cursor.fetchone()
        return AVInfo.generate_from_db(result) if result else None

    def create_or_update_avinfo(self, avinfo: AVInfo) -> bool:
        avid = avinfo.get_avid()
        title = avinfo.get_title()
        source = avinfo.get_source()
        duration = avinfo.get_duration()
        release_date = avinfo.get_release_date()
        producer = avinfo.get_producer()
        publisher = avinfo.get_publisher()
        series = avinfo.get_series()
        category = avinfo.get_category()
        actors = avinfo.get_actors()
        image_url = avinfo.get_image_url()
        try:
            self._cursor.execute("""
                                 select avid, source
                                 from AVInfo
                                 where avid = ?
                                   and source = ?
                                 """, (avinfo.get_avid(), avinfo.get_source()))
            if self._cursor.fetchone() is None:
                self._cursor.execute("""
                                     insert into AVInfo(avid, title, source, release_date, duration,
                                                        producer, publisher, series, category, actors, image_url)
                                     values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                     """, (avid, title, source, release_date, duration,
                                           producer, publisher, series, category, actors, image_url))
            else:
                self._cursor.execute("""
                                     update AVInfo
                                     set title        = ?,
                                         release_date = ?,
                                         duration     = ?,
                                         producer     = ?,
                                         publisher    = ?,
                                         series       = ?,
                                         category     = ?,
                                         actors       = ?,
                                         image_url    = ?
                                     where avid = ?
                                       and source = ?
                                     """, (title, release_date, duration, producer,
                                           publisher, series, category, actors, image_url, avid, source))
            self._database.commit()
        except sql.OperationalError as e:
            logger.error(f"Error in create_or_update_avinfo: {e}")
            return False
        return True


avinfo_repo = AVInfoRepo()
