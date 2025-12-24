from nonebot import require
from nonebot.log import logger

from .model import AVInfo

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import *

require("nonebot_plugin_uninfo")
from nonebot_plugin_uninfo import *

from .scraper.ScraperManager import scraper_manager

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-flo-jav",
    description="Florenz的JAV元数据查询插件。",
    usage="""
    jav.q avid 查询番号为avid的元数据
    """,
    homepage="https://github.com/Florenz0707/nonebot-plugin-flo-jav",
    type="application",
    config=Config,
    supported_adapters={"~onebot.v11"},
    extra={
        "author": "florenz0707",
    }
)


async def intro_sender(info: AVInfo, uid: str):
    content = (UniMessage.text(info.to_string()).
               image(path=scraper_manager.get_image_path(info.get_avid())))
    node = CustomNode(uid=uid, name="", content=content)
    try:
        await UniMessage.reference(node).finish()
    except Exception as error:
        error = str(error)
        if "发送转发消息" in error and "失败" in error:
            await UniMessage.text(f"[{info.get_avid()}]发送转发消息失败了！").finish()


query = on_alconna(
    Alconna(
        "jav.q",
        Args["avid", str],
    ),
    use_cmd_start=True,
)


@query.handle()
async def abstract_handler(
        session: Uninfo,
        avid: Match[str] = AlconnaMatch("avid")):
    if not avid.available:
        await UniMessage.text("听不懂哦~ 再试一次吧~").finish()
    avid = avid.result.upper()
    info = await scraper_manager.scrape_from_any(avid)
    if info is None:
        await UniMessage.text("获取失败了！").finish()
    await intro_sender(info, session.self_id)
