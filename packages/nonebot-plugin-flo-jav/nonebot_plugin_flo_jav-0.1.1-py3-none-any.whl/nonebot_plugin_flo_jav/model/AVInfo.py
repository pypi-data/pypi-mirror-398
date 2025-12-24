from typing import Optional


class AVInfo:
    def __init__(self):
        self._avid: Optional[str] = ""
        self._title: Optional[str] = ""
        self._source: Optional[str] = ""
        self._release_date: Optional[str] = ""
        self._duration: Optional[str] = ""
        self._producer: Optional[str] = ""
        self._publisher: Optional[str] = ""
        self._series: Optional[str] = ""
        self._category: Optional[str] = ""
        self._actors: Optional[str] = ""
        self._image_url: Optional[str] = ""

    def get_avid(self) -> Optional[str]:
        return self._avid

    def get_title(self) -> Optional[str]:
        return self._title

    def get_source(self) -> Optional[str]:
        return self._source

    def get_release_date(self) -> Optional[str]:
        return self._release_date

    def get_duration(self) -> Optional[str]:
        return self._duration

    def get_producer(self) -> Optional[str]:
        return self._producer

    def get_publisher(self) -> Optional[str]:
        return self._publisher

    def get_series(self) -> Optional[str]:
        return self._series

    def get_category(self) -> Optional[str]:
        return self._category

    def get_actors(self) -> Optional[str]:
        return self._actors

    def get_image_url(self) -> Optional[str]:
        return self._image_url

    @classmethod
    def generate_from_scrapper(cls, scrape_data: dict):
        """
        从刮削器数据更新元数据
        :param scrape_data:
        :return:
        """
        info = AVInfo()
        if scrape_data.get("avid"):
            info._avid = scrape_data.get("avid")
        if scrape_data.get("title"):
            info._title = scrape_data.get("title")
        if scrape_data.get("source"):
            info._source = scrape_data.get("source")
        if scrape_data.get('release_date'):
            info._release_date = scrape_data.get('release_date')
        if scrape_data.get('duration'):
            info._duration = scrape_data.get('duration')
        if scrape_data.get('producer'):
            info._producer = scrape_data.get('producer')
        if scrape_data.get('publisher'):
            info._publisher = scrape_data.get('publisher')
        if scrape_data.get('series'):
            info._series = scrape_data.get('series')
        if scrape_data.get('category'):
            info._category = scrape_data.get('category')
        if scrape_data.get('actors'):
            info._actors = scrape_data.get('actors')
        if scrape_data.get('image_url'):
            info._image_url = scrape_data.get('image_url')
        return info

    @classmethod
    def generate_from_db(cls, data: tuple[str, str, str, str, str, str, str, str, str, str, str]):
        result = AVInfo()
        result._avid = data[0]
        result._title = data[1]
        result._source = data[2]
        result._release_date = data[3]
        result._duration = data[4]
        result._producer = data[5]
        result._publisher = data[6]
        result._series = data[7]
        result._category = data[8]
        result._actors = data[9]
        result._image_url = data[10]
        return result

    def to_string(self):
        return f"AVID：{self._avid}\n标题：{self._title}\n来源：{self._source}\n发行日期：{self._release_date}\n" \
               f"时长：{self._duration}\n制作：{self._producer}\n发行：{self._publisher}\n系列：{self._series}\n" \
               f"类别：{self._category}\n演员：{self._actors}"
