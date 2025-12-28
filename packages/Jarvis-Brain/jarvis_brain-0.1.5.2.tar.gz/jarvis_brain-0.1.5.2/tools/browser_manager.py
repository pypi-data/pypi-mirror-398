"""浏览器池管理模块 - 单例模式确保状态共享"""
import random
from typing import Optional, Tuple
import os
from DrissionPage import ChromiumPage, ChromiumOptions


class BrowserManager:
    """浏览器池管理器 - 使用单例模式"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.browser_pool = {}
        return cls._instance

    def create_browser(self) -> Tuple[int, ChromiumPage]:
        """创建新的浏览器实例"""
        random_port = random.randint(9223, 9934)
        while random_port in self.browser_pool:
            random_port = random.randint(9223, 9934)

        co = ChromiumOptions().set_local_port(random_port)
        custom_data_dir = os.path.join(os.path.expanduser('~'), 'DrissionPage', "userData", f"{random_port}")

        # 2. 配置浏览器选项，指定该目录
        # co = ChromiumOptions()
        co.set_user_data_path(custom_data_dir)  # 设置用户数据路径
        self.browser_pool[random_port] = ChromiumPage(co)
        return random_port, self.browser_pool[random_port]

    def get_browser(self, port: int) -> Optional[ChromiumPage]:
        """根据端口获取浏览器实例"""
        return self.browser_pool.get(port)

    def remove_browser(self, port: int) -> Tuple[bool, Optional[ChromiumPage]]:
        """根据端口移除浏览器实例"""
        browser = self.browser_pool.pop(port, None)
        return browser is not None, browser

    def list_browsers(self) -> list[int]:
        """列出所有活跃的浏览器端口"""
        return list(self.browser_pool.keys())


# 创建全局单例实例
browser_manager = BrowserManager()
