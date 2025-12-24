from pathlib import Path

from pydantic import BaseModel

from nonebot import get_plugin_config, require

require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as localstore

data_dir: Path = localstore.get_plugin_data_dir()
database_file: Path = data_dir / 'flo_jav.db'


class Config(BaseModel):
    jav_proxy: str = None


jav_config = get_plugin_config(Config)
