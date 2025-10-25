import sys
import logging
from typing import Optional
import config
from developer1_input_handler import process_input
from developer2_map_automation import execute_navigation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NavigationCoordinator:
    
    def __init__(self):
        self.api_key = config.ANTHROPIC_API_KEY
        self.default_map_service = config.DEFAULT_MAP_SERVICE
        
    def validate_config(self) -> bool:
        if not self.api_key:
            logger.error("错误: 未设置 ANTHROPIC_API_KEY")
            logger.info("请在 .env 文件中配置 ANTHROPIC_API_KEY")
            return False
        return True
    
    def run(self, input_type: str = "text"):
        if not self.validate_config():
            return False
        
        logger.info("=" * 50)
        logger.info("AI 驱动的地图导航系统")
        logger.info("=" * 50)
        
        try:
            logger.info(f"输入模式: {input_type}")
            navigation_info = process_input(input_type, self.api_key)
            
            if not navigation_info:
                logger.error("无法获取导航信息")
                return False
            
            logger.info(f"导航信息: {navigation_info}")
            
            success = execute_navigation(navigation_info)
            
            if success:
                logger.info("导航任务完成")
                return True
            else:
                logger.error("导航任务失败")
                return False
                
        except KeyboardInterrupt:
            logger.info("\n用户中断操作")
            return False
        except Exception as e:
            logger.error(f"系统错误: {e}", exc_info=True)
            return False


def print_usage():
    print("""
使用方法:
    python developer3_main_coordinator.py [选项]
    
选项:
    --text      使用文本输入 (默认)
    --voice     使用语音输入
    --help      显示帮助信息
    
示例:
    python developer3_main_coordinator.py --text
    python developer3_main_coordinator.py --voice
    
配置:
    1. 复制 .env.example 为 .env
    2. 在 .env 中配置必要的 API 密钥
    3. 安装依赖: pip install -r requirements.txt
    4. 安装 Playwright 浏览器: playwright install chromium
""")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print_usage()
        return
    
    input_type = "text"
    if len(sys.argv) > 1:
        if sys.argv[1] == "--voice":
            input_type = "voice"
        elif sys.argv[1] == "--text":
            input_type = "text"
        else:
            print(f"未知选项: {sys.argv[1]}")
            print_usage()
            return
    
    coordinator = NavigationCoordinator()
    coordinator.run(input_type)


if __name__ == "__main__":
    main()
