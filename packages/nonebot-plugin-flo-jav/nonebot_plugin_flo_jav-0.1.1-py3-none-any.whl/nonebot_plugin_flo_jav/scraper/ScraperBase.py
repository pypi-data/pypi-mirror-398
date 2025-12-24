"""
Scraper 基类 - 定义刮削器的通用接口和方法
"""
from typing import Optional

from curl_cffi import requests
from pathlib import Path
from nonebot.log import logger

from ..model import AVInfo
from ..constants import HEADERS, IMPERSONATE


class ScraperBase:
    """刮削器基类"""

    def __init__(self, proxy: Optional[str] = None, timeout: int = 15):
        self.proxy = proxy
        self.proxies = {'http': proxy, 'https': proxy} if proxy else None
        self.timeout = timeout
        self.domain = ""

    def set_domain(self, domain: str):
        """设置域名"""
        self.domain = domain

    def get_domain(self) -> str:
        return self.domain

    def get_scraper_name(self) -> str:
        """获取刮削器名称，子类必须实现"""
        raise NotImplementedError

    async def get_html(self, avid: str) -> Optional[str]:
        """根据 avid 获取 HTML，子类必须实现"""
        raise NotImplementedError

    def parse_html(self, html: str, avid: str) -> Optional[dict]:
        """解析 HTML 获取元数据，子类必须实现"""
        raise NotImplementedError

    async def fetch_html(self, url: str) -> Optional[str]:
        """获取 HTML 页面"""
        logger.info(f"Scraper fetch url: {url}")
        try:
            async with requests.AsyncSession() as session:
                response = await session.get(
                    url,
                    proxies=self.proxies,
                    headers=HEADERS,
                    timeout=self.timeout,
                    impersonate=IMPERSONATE,
                )
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Scraper 请求失败: {str(e)}")
            return None

    async def scrape(self, avid: str) -> Optional[AVInfo]:
        """
        刮削元数据
        返回包含元数据的字典或 None
        """
        avid = avid.upper()
        if html := await self.get_html(avid):
            if metadata := self.parse_html(avid, html):
                logger.info(f"成功从 {self.get_scraper_name()} 获取 {avid} 的元数据")
                return AVInfo.generate_from_scrapper(metadata)
        return None

    async def download_image(self, image_url: str, save_path: Path) -> bool:
        """
        下载图片并保存到指定路径

        :param image_url: 图片 URL（可以是相对路径或绝对路径）
        :param save_path: 保存路径
        :return: 成功返回 True，失败返回 False
        """
        try:
            # 处理相对路径 URL
            if image_url.startswith('/'):
                full_url = f"https://{self.domain}{image_url}"
            elif not image_url.startswith('http'):
                full_url = f"https://{self.domain}/{image_url}"
            else:
                full_url = image_url

            logger.info(f"下载图片: {full_url}")

            # 创建保存目录
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # 创建图片下载专用的 headers，添加 Referer 防止防盗链
            image_headers = HEADERS.copy()
            image_headers['Referer'] = f"https://{self.domain}/"
            image_headers['Accept'] = 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'

            # 下载图片
            async with requests.AsyncSession() as session:
                response = await session.get(
                    full_url,
                    proxies=self.proxies,
                    headers=image_headers,
                    timeout=self.timeout,
                    impersonate=IMPERSONATE,
                )
                response.raise_for_status()

                # 保存图片
                with open(save_path, 'wb') as f:
                    f.write(response.content)

                logger.info(f"图片已保存: {save_path} ({len(response.content)} 字节)")
                return True

        except Exception as e:
            logger.error(f"下载图片失败: {str(e)}")
            return False
