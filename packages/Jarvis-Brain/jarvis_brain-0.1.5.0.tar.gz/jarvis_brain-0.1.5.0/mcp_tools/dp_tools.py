import json
import os
from typing import Any

from DrissionPage._elements.none_element import NoneElement
from fastmcp import FastMCP

from tools.tools import compress_html, requests_html, dp_headless_html, assert_waf_cookie, dp_mcp_message_pack

html_source_code_local_save_path = os.path.join(os.getcwd(), "html-source-code")
waf_status_code_dict = {
    412: "瑞数",
    521: "加速乐"
}


def register_visit_url(mcp: FastMCP, browser_manager):
    @mcp.tool(name="visit_url", description="使用Drissionpage打开url访问某个网站")
    async def visit_url(url: str) -> dict[str, Any]:
        port, _browser = browser_manager.create_browser()
        tab = _browser.get_tab()
        tab.get(url)
        tab_id = tab.tab_id
        return dp_mcp_message_pack(
            f"已在[{port}]端口创建浏览器对象，并已打开链接：{url}",
            tab_id=tab_id,
            browser_port=port
        )


def register_get_html(mcp: FastMCP, browser_manager):
    @mcp.tool(name="get_html", description="使用Drissionpage获取某一个tab页的html")
    async def get_html(browser_port: int, tab_id: str) -> dict[str, Any]:
        _browser = browser_manager.get_browser(browser_port)
        tab = _browser.get_tab(tab_id)
        file_name = tab.title + f"_{tab_id}.html"
        if not os.path.exists(html_source_code_local_save_path):
            os.makedirs(html_source_code_local_save_path)
        abs_path = os.path.join(html_source_code_local_save_path, file_name)
        with open(abs_path, "w", encoding="utf-8") as f:
            min_html, compress_rate = compress_html(tab.html)
            f.write(min_html)
        return dp_mcp_message_pack(f"已保存tab页：【{tab_id}】的html源码", tab_id=tab_id, html_local_path=abs_path)


def register_get_new_tab(mcp: FastMCP, browser_manager):
    @mcp.tool(name="get_new_tab", description="使用Drissionpage创建一个新的tab页，在新的tab页中打开url")
    async def get_new_tab(browser_port: int, url: str) -> dict[str, Any]:
        _browser = browser_manager.get_browser(browser_port)
        tab = _browser.new_tab(url)
        _browser.activate_tab(tab)
        tab_id = tab.tab_id
        return dp_mcp_message_pack(f"已创建新的tab页，并打开链接：{url}", tab_id=tab_id)


def register_switch_tab(mcp: FastMCP, browser_manager):
    @mcp.tool(name="switch_tab", description="根据传入的tab_id切换到对应的tab页", )
    async def switch_tab(browser_port: int, tab_id: str) -> dict[str, Any]:
        _browser = browser_manager.get_browser(browser_port)
        _browser.activate_tab(tab_id)
        return dp_mcp_message_pack(f"已将tab页:【{tab_id}】切换至最前端")


def register_close_tab(mcp: FastMCP, browser_manager):
    @mcp.tool(name="close_tab", description="根据传入的tab_id关闭tab页", )
    async def close_tab(browser_port, tab_id) -> dict[str, Any]:
        _browser = browser_manager.get_browser(browser_port)
        _browser.close_tabs(tab_id)
        return dp_mcp_message_pack(f"已将tab页:【{tab_id}】关闭")


def register_check_selector(mcp: FastMCP, browser_manager):
    @mcp.tool(name="check_selector", description="查找tab页中是否包含元素，并返回元素attr_name所对应的值")
    async def check_selector(browser_port: int, tab_id: str, css_selector: str, attr_name: str = "text") -> dict[str, Any]:
        _browser = browser_manager.get_browser(browser_port)
        target_tab = _browser.get_tab(tab_id)
        css_selector = css_selector
        if "css:" not in css_selector:
            css_selector = "css:" + css_selector
        target_eles = target_tab.eles(css_selector)
        exist_flag = False
        if len(target_eles) != 0:
            exist_flag = True
        if attr_name == "text":
            ele_text_list = [i.text.replace("\n", "") for i in target_eles]
            attr_output = "\n".join(ele_text_list)
        else:
            attr_output = json.dumps([i.attr(attr_name) for i in target_eles])
        return dp_mcp_message_pack(
            f"已完成tab页:【{tab_id}】对：【{css_selector}】的检查",
            tab_id=tab_id,
            selector=css_selector,
            selector_ele_exist=exist_flag,
            attr_output=attr_output
        )


def register_quit_browser(mcp: FastMCP, browser_manager):
    @mcp.tool(name="quit_browser", description="退出浏览器会话，关闭浏览器")
    async def quit_browser(browser_port: int) -> dict[str, Any]:
        flag, _browser = browser_manager.remove_page(browser_port)
        if flag:
            _browser.quit()
        return dp_mcp_message_pack(
            f"浏览器[{browser_port}]，退出会话，关闭浏览器{'成功' if flag else '失败'}",
            browser_port=browser_port,
            quit_flag=flag
        )


def register_assert_waf(mcp: FastMCP, browser_manager):
    @mcp.tool(name="assert_waf",
              description="通过对比requests、有头浏览器、无头浏览器获取到的html，判断网页是否使用了waf以及是否为动态渲染的网页")
    async def assert_waf(browser_port: int, tab_id: str) -> dict[str, Any]:
        _browser = browser_manager.get_browser(browser_port)
        target_tab = _browser.get_tab(tab_id)
        recommend_team = "drissionpage_head"
        head_cookies = target_tab.cookies()
        # 通过cookie判断是否有waf
        waf_flag, waf_type = assert_waf_cookie(head_cookies)
        head_html = target_tab.html
        min_head_html, head_rate = compress_html(head_html, only_text=True)
        raw_html, status_code = requests_html(target_tab.url)
        min_raw_html, raw_rate = compress_html(raw_html, only_text=True)
        r_h_rate_diff = abs(head_rate - raw_rate)
        # 如果有已知的防火墙，则不浪费时间使用无头获取html和压缩比了
        if waf_flag or status_code in waf_status_code_dict.keys():
            return dp_mcp_message_pack(
                f"已完成tab页:【{tab_id}】的分析，该tab页存在waf",
                tab_id=tab_id,
                recommend_team=recommend_team,
                raw_head_rate_difference=r_h_rate_diff,
                raw_headless_rate_difference=0,
                head_headless_rate_difference=0
            )

        headless_html = dp_headless_html(target_tab.url)
        min_headless_html, headless_rate = compress_html(headless_html, only_text=True)
        r_hless_rate_diff = abs(raw_rate - headless_rate)
        h_hless_rate_diff = abs(head_rate - headless_rate)
        # 最优情况：requests，dp有头和无头拿到的结果基本一致，认定为没有防护的静态网页
        if r_h_rate_diff < 40 and r_hless_rate_diff < 40 and h_hless_rate_diff < 40:
            recommend_team = "requests"
        # 最差情况：requests，dp有头和无头拿到的结果差距都很大，认定为有浏览器无头检测+动态网页
        # if r_h_rate_diff < 40 and r_hless_rate_diff < 40 and h_hless_rate_diff < 40:
        # 较差1：dp有头和无头差距很小，但是requests拿不到正确结果，认定为有requests防护 or 动态网页
        elif h_hless_rate_diff < 30 and r_hless_rate_diff > 40:
            recommend_team = "drissionpage_headless"
        # 较差2：有头和无头差距很大，但是requests和有头拿到的结果基本一致，认定为要么有别的没有防护requests的waf，或者间歇性的瑞数【此时应该拿有头的cookie去判断其中是否有瑞数特征，上面已经做了】
        # if r_h_rate_diff < 15 and h_hless_rate_diff > 40:
        return dp_mcp_message_pack(
            f"已完成tab页:【{tab_id}】的分析，该tab页存在waf",
            tab_id=tab_id,
            recommend_team=recommend_team,
            raw_head_rate_difference=r_h_rate_diff,
            raw_headless_rate_difference=h_hless_rate_diff,
            head_headless_rate_difference=h_hless_rate_diff
        )

# def register_highlight_element_captcha(mcp: FastMCP, browser_manager):
#     @mcp.tool(name="highlight_element_captcha",
#               description="将传入的Selector在页面上高亮，并截屏")
#     async def highlight_element_captcha(browser_port: int, tab_id: str, selector: str) -> dict[str, Any]:
#         _browser = browser_manager.get_browser(browser_port)
#         tab = _browser.get_tab(tab_id)
#         tab.ele
