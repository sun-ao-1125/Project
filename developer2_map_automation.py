from playwright.sync_api import sync_playwright, Page, Browser
import logging
import time
from typing import Dict
import urllib.parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MapAutomation:
    
    def __init__(self):
        self.browser: Browser = None
        self.page: Page = None
        self.playwright = None
        
    def start_browser(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()
        logger.info("浏览器已启动")
        
    def close_browser(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("浏览器已关闭")


class BaiduMapAutomation(MapAutomation):
    
    BASE_URL = "https://map.baidu.com"
    
    def navigate(self, origin: str, destination: str):
        try:
            logger.info(f"使用百度地图: {origin} -> {destination}")
            
            origin_encoded = urllib.parse.quote(origin)
            dest_encoded = urllib.parse.quote(destination)
            
            url = f"{self.BASE_URL}/direction?origin={origin_encoded}&destination={dest_encoded}&mode=driving&output=html"
            
            logger.info(f"正在打开百度地图: {url}")
            self.page.goto(url, timeout=30000)
            
            time.sleep(2)
            
            logger.info("正在查找导航按钮...")
            try:
                nav_button = self.page.locator('text="开始导航"').first
                if nav_button.is_visible():
                    nav_button.click()
                    logger.info("已点击开始导航")
                else:
                    logger.info("未找到导航按钮，路线已显示")
            except Exception as e:
                logger.warning(f"点击导航按钮失败: {e}")
                logger.info("路线规划已显示在页面上")
            
            logger.info("百度地图导航设置完成")
            return True
            
        except Exception as e:
            logger.error(f"百度地图自动化失败: {e}")
            return False


class GaodeMapAutomation(MapAutomation):
    
    BASE_URL = "https://www.amap.com"
    
    def navigate(self, origin: str, destination: str):
        try:
            logger.info(f"使用高德地图: {origin} -> {destination}")
            
            origin_encoded = urllib.parse.quote(origin)
            dest_encoded = urllib.parse.quote(destination)
            
            url = f"{self.BASE_URL}/dir?from={origin_encoded}&to={dest_encoded}&type=car"
            
            logger.info(f"正在打开高德地图: {url}")
            self.page.goto(url, timeout=30000)
            
            time.sleep(2)
            
            logger.info("正在查找导航按钮...")
            try:
                nav_button = self.page.locator('text="开始导航"').first
                if nav_button.is_visible():
                    nav_button.click()
                    logger.info("已点击开始导航")
                else:
                    logger.info("未找到导航按钮，路线已显示")
            except Exception as e:
                logger.warning(f"点击导航按钮失败: {e}")
                logger.info("路线规划已显示在页面上")
            
            logger.info("高德地图导航设置完成")
            return True
            
        except Exception as e:
            logger.error(f"高德地图自动化失败: {e}")
            return False


class MapServiceFactory:
    
    @staticmethod
    def create_map_service(service_name: str) -> MapAutomation:
        if service_name.lower() == "baidu":
            return BaiduMapAutomation()
        elif service_name.lower() in ["gaode", "amap"]:
            return GaodeMapAutomation()
        else:
            logger.warning(f"未知的地图服务: {service_name}，使用默认百度地图")
            return BaiduMapAutomation()


def execute_navigation(navigation_info: Dict[str, str]) -> bool:
    origin = navigation_info.get('origin', '')
    destination = navigation_info.get('destination', '')
    map_service = navigation_info.get('map_service', 'baidu')
    
    if not origin or not destination:
        logger.error("起点或终点信息不完整")
        return False
    
    map_automation = MapServiceFactory.create_map_service(map_service)
    
    try:
        map_automation.start_browser()
        success = map_automation.navigate(origin, destination)
        
        if success:
            logger.info("导航已启动，浏览器将保持打开状态")
            input("按回车键关闭浏览器...")
        
        return success
        
    finally:
        map_automation.close_browser()
