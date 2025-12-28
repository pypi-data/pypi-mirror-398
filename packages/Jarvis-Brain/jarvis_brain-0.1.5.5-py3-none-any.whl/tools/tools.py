import time
import random
import os
import minify_html
from DrissionPage import ChromiumPage, ChromiumOptions
from bs4 import BeautifulSoup
from curl_cffi import requests
from lxml import html, etree


# 使用requests获取html，用于测试是否使用了瑞数和jsl
def requests_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    }
    response = requests.get(url, headers=headers, verify=False)
    response.encoding = "utf-8"
    return response.text, response.status_code


# 使用dp无头模式获取html，用于测试是否使用了其他waf，如移动waf
def dp_headless_html(url):
    opt = ChromiumOptions().headless(True)
    opt.set_argument('--no-sandbox')
    """创建新的浏览器实例"""
    random_port = random.randint(9934, 10034)
    custom_data_dir = os.path.join(os.path.expanduser('~'), 'DrissionPage', "userData", f"{random_port}")
    opt.set_user_data_path(custom_data_dir)  # 设置用户数据路径
    opt.set_local_port(random_port)
    page = ChromiumPage(opt)
    tab = page.latest_tab
    tab.get(url)
    # todo: 目前没有更好的方式，为了数据渲染完全，只能硬等【受网速波动影响比较大】
    time.sleep(10)
    page_html = tab.html
    # 无头浏览器在用完之后一定要记得再page级别进行quit
    page.quit()
    return page_html


# 压缩html
def compress_html(content, only_text=False):
    doc = html.fromstring(content)
    # 删除 style 和 script 标签
    for element in doc.xpath('//style | //script'):
        element.getparent().remove(element)

    # 删除 link 标签
    for link in doc.xpath('//link[@rel="stylesheet"]'):
        link.getparent().remove(link)

    # 删除 meta 标签（新增功能）
    for meta in doc.xpath('//meta'):
        meta.getparent().remove(meta)

    # 删除 style 属性
    for element in doc.xpath('//*[@style]'):
        element.attrib.pop('style')

    # 删除所有 on* 事件属性
    for element in doc.xpath('//*'):
        for attr in list(element.attrib.keys()):
            if attr.startswith('on'):
                element.attrib.pop(attr)

    result = etree.tostring(doc, encoding='unicode')
    result = minify_html.minify(result)
    compress_rate = round(len(content) / len(result) * 100)
    print(f"html压缩比=> {compress_rate}%")
    if not only_text:
        return result, compress_rate
    soup = BeautifulSoup(result, 'html.parser')
    result = soup.get_text(strip=True)
    return result, compress_rate


# 通过cookie判断是否有waf，需要通过遇到的例子，不断的完善cookie判别函数
def assert_waf_cookie(cookies: list):
    for cookie in cookies:
        cookie_name = cookie['name']
        cookie_value = cookie['value']
        if len(cookie_name) == 13 and len(cookie_value) == 88:
            return True, "瑞数"
        if "_jsl" in cookie_name:
            return True, "加速乐"
    return False, "没有waf"


# 对dp_mcp的消息打包
def dp_mcp_message_pack(message: str, **kwargs):
    text_obj = {key: value for key, value in kwargs.items()}
    text_obj.update({"message": message})
    return {
        "content": [{
            "type": "text",
            # "text": json.dumps(text_obj, ensure_ascii=False)
            "text": text_obj
        }]
    }

# todo: 大致盘一下各种判定的逻辑【以下的所有压缩比之间的差距均取“绝对值”】
#  1. 如果requests、无头、有头获取到的压缩比之间从差距都在15%以内，则认定该页面是静态页面，此时优先使用requests请求
#  2. 如果requests的status_code为特定的412，或者521，则判定是瑞数和jsl。[此时还有一个特点：requests的压缩比会与其他两种方式获取到的压缩比差距非常大(一两千的那种)]
#  3. 如果requests、无头、有头获取到的压缩比之间差距都在40%以上，则判定该页面只可以用有头采集
#  4. 如果无头和有头获取到的压缩比之间差距小于15%，但是requests和无头的差距大于40%，则认定该页面可以使用无头浏览器采集
#  5. 如果requests和有头获取到的压缩比之间差距小于15%，但是无头和有头的差距大于40%，则认定该页面优先使用有头浏览器采集
#  【此时可能是：1.使用了别的检测无头的waf。2.网站使用瑞数，但是这次请求没有拦截requests（不知道是不是瑞数那边故意设置的），
#   此时如果想进一步判定是否是瑞数，可以使用有头浏览器取一下cookies，如果cookies里面存在瑞数的cookie，那么就可以断定是瑞数】
