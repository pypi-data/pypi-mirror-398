"""
Scraper 管理器 - 管理所有刮削器的注册和调用
"""
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from nonebot.log import logger

from .ScraperBase import ScraperBase
from .Javbus import Javbus, Busdmm, Dmmsee
from ..model import AVInfo
from ..repository.AVInfoRepo import avinfo_repo

from ..config import jav_config, data_dir


class ScraperManager:
    """刮削器管理器"""

    # 刮削器类映射
    SCRAPER_CLASSES = {
        'javbus': Javbus,
        'busdmm': Busdmm,
        'dmmsee': Dmmsee
    }

    def __init__(self,
                 proxy: Optional[str] = None,
                 image_path: Optional[Path] = None):
        self.proxy = proxy
        self.image_path = image_path
        self.avinfo_repo = avinfo_repo
        self.scrapers: Dict[str, ScraperBase] = {}
        for name, scraper in self.SCRAPER_CLASSES.items():
            scraper = scraper(proxy)
            self.scrapers[scraper.get_scraper_name()] = scraper
            logger.info(f"注册刮削器: {scraper.get_scraper_name()}, 域名: {scraper.get_domain()}")

    def get_scrapers(self) -> List[Tuple[str, ScraperBase]]:
        """获取所有已注册的刮削器列表"""
        return [(name, scraper) for name, scraper in self.scrapers.items()]

    async def scrape_from_any(self, avid: str) -> Optional[AVInfo]:
        """
        遍历所有刮削器获取元数据
        返回第一个成功获取的元数据
        """
        avid = avid.upper()
        if metadata := await self._load_cache(avid):
            return metadata
        for name, scraper in self.get_scrapers():
            metadata = await self._scrape(avid, scraper)
            return metadata
        logger.warning(f"无法从任何刮削源获取 {avid} 的元数据")
        return None

    async def scrape_from_specific(self, avid: str, scraper_name: str) -> Optional[AVInfo]:
        """
        从指定的刮削器获取元数据
        """
        avid = avid.upper()
        if metadata := await self._load_cache(avid):
            return metadata
        scraper = self.scrapers.get(scraper_name)
        if scraper:
            metadata = await self._scrape(avid, scraper)
            return metadata
        return None

    def get_image_path(self, avid: str) -> Optional[Path]:
        return self.image_path / avid.upper()

    async def _load_cache(self, avid: str) -> Optional[AVInfo]:
        if metadata := self.avinfo_repo.get_from_source(avid, None):
            if not self.get_image_path(avid).exists():
                scraper = self.scrapers[metadata.get_scraper_name()]
                if not await scraper.download_image(metadata.get_image_url(), self.get_image_path(avid)):
                    logger.warning(f"下载封面失败：{metadata.get_image_url()}")
                    return None
            return metadata
        return None

    async def _scrape(self, avid: str, scraper: ScraperBase) -> Optional[AVInfo]:
        if metadata := await scraper.scrape(avid):
            self.avinfo_repo.create_or_update_avinfo(metadata)
            logger.info(f"成功从{scraper.get_scraper_name()}刮削数据！准备下载封面图......")
            if await scraper.download_image(metadata.get_image_url(), self.get_image_path(avid)):
                return metadata
        return None


scraper_manager = ScraperManager(
    jav_config.jav_proxy,
    data_dir / "image"
)
