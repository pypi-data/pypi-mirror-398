from fastmcp import FastMCP

from mcp_tools.dp_tools import *
from tools.browser_manager import browser_manager

mcp = FastMCP("Jarvis Brain Mcp Tools")

# 根据环境变量加载模块
enabled_modules = os.getenv("MCP_MODULES", "TeamNode-Dp").split(",")
base_cwd = os.getenv("BASE_CWD", os.environ.get("PWD"))

if "TeamNode-Dp" in enabled_modules:
    # 页面管理
    register_close_tab(mcp, browser_manager)
    register_switch_tab(mcp, browser_manager)
    register_get_new_tab(mcp, browser_manager)
    # 功能
    register_visit_url(mcp, browser_manager)
    register_get_html(mcp, browser_manager)
    register_check_selector(mcp, browser_manager)

if "JarvisNode" in enabled_modules:
    register_assert_waf(mcp, browser_manager)


def main():
    mcp.run(transport="stdio")


if __name__ == '__main__':
    main()
