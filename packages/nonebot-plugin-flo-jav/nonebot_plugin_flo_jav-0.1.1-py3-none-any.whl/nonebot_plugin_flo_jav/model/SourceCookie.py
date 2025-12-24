from datetime import datetime


class SourceCookie:

    def __init__(self):
        self._source: str | None = None
        self._cookie: str | None = None
        self._updated_at: str | None = None

    def get_source(self):
        return self._source

    def get_cookie(self):
        return self._cookie

    def get_updated_at(self):
        return self._updated_at

    @classmethod
    def generate_from_source(cls, cookie_dict: dict):
        """
        cookie_dict should have "source" and "cookie"
        :param cookie_dict:
        :return:
        """
        result = SourceCookie()
        if cookie_dict.get("source") is None:
            return None
        result.source = cookie_dict["source"]

        if cookie_dict.get("cookie") is None:
            return None
        result.cookie = cookie_dict["cookie"]
        result.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return result

    @classmethod
    def generate_from_db(cls, data: tuple[str, str, str]):
        result = SourceCookie()
        result.source = data[0]
        result.cookie = data[1]
        result.updated_at = data[2]
        return result
