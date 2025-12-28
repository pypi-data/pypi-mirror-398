# Jarvis Brain MCP

<div align="center">

一个基于 FastMCP 和 DrissionPage 的浏览器自动化 MCP 服务器

[![Python Version](https://img.shields.io/badge/python-3.10~3.12-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.4.5-green.svg)](https://github.com/yourusername/jarvis-mcp)

## 📖 简介

Jarvis Brain MCP 是一个强大的浏览器自动化工具，通过 Model Context Protocol (MCP) 提供服务。它集成了 DrissionPage 浏览器控制能力，支持多浏览器实例管理、智能 WAF 检测、HTML 获取与压缩等功能，特别适用于网页爬取、自动化测试和反爬虫分析场景。

## ✨ 核心特性

### 🌐 浏览器管理
- **多实例浏览器池**: 使用单例模式管理多个浏览器实例，支持并发操作
- **标签页控制**: 创建、切换、关闭标签页，灵活管理浏览器标签
- **智能端口分配**: 自动分配随机端口 (9223-9934)，避免端口冲突

### 🛡️ WAF 检测
- **多维度检测**: 对比 requests、有头浏览器、无头浏览器三种方式获取的 HTML
- **Cookie 特征识别**: 自动识别瑞数、加速乐等常见 WAF 的 Cookie 特征
- **智能推荐**: 根据检测结果推荐最适合的采集方案（requests / headless / head）

### 📄 HTML 处理
- **智能压缩**: 自动移除 style、script、meta 标签及相关属性
- **压缩比计算**: 实时计算压缩率，用于 WAF 检测判断
- **本地保存**: 将获取的 HTML 保存到本地，便于后续分析

### 🔍 元素检测
- **CSS 选择器支持**: 检测页面中是否存在指定的 CSS 选择器元素
- **智能格式化**: 自动添加 `css:` 前缀，简化使用

## 🚀 快速开始

### 安装

```bash
pip install Jarvis_Brain
```

或从源码安装：

```bash
git clone https://github.com/yourusername/jarvis-mcp.git
cd jarvis-mcp
pip install -e .
```

## 🛠️ MCP 工具列表

### TeamNode-Dp 模块

#### 1. visit_url
打开指定 URL 并创建浏览器实例。

**参数:**
- `url` (str): 要访问的网页 URL

**返回:**
- `message`: 操作结果消息
- `tab_id`: 标签页 ID
- `browser_port`: 浏览器端口号

#### 2. get_html
获取指定标签页的 HTML 源码并保存到本地。

**参数:**
- `browser_port` (int): 浏览器端口号
- `tab_id` (str): 标签页 ID

**返回:**
- `message`: 操作结果消息
- `tab_id`: 标签页 ID
- `html_local_path`: HTML 文件保存路径

#### 3. get_new_tab
在指定浏览器中创建新标签页并打开 URL。

**参数:**
- `browser_port` (int): 浏览器端口号
- `url` (str): 要访问的 URL

**返回:**
- `message`: 操作结果消息
- `tab_id`: 新标签页 ID

#### 4. switch_tab
切换到指定的标签页。

**参数:**
- `browser_port` (int): 浏览器端口号
- `tab_id` (str): 要切换到的标签页 ID

**返回:**
- `message`: 操作结果消息

#### 5. close_tab
关闭指定的标签页。

**参数:**
- `browser_port` (int): 浏览器端口号
- `tab_id` (str): 要关闭的标签页 ID

**返回:**
- `message`: 操作结果消息

#### 6. check_selector
检查标签页中是否存在指定的 CSS 选择器元素。

**参数:**
- `browser_port` (int): 浏览器端口号
- `tab_id` (str): 标签页 ID
- `css_selector` (str): CSS 选择器

**返回:**
- `message`: 操作结果消息
- `tab_id`: 标签页 ID
- `selector`: 完整的选择器
- `selector_ele_exist` (bool): 元素是否存在

### JarvisNode 模块

#### 7. assert_waf
智能检测网页是否使用了 WAF 及页面渲染类型。

**检测原理:**
1. 通过 Cookie 特征识别已知 WAF（瑞数、加速乐等）
2. 对比 requests、无头浏览器、有头浏览器获取的 HTML 压缩比
3. 根据压缩比差异判断页面类型和推荐采集方案

**参数:**
- `browser_port` (int): 浏览器端口号
- `tab_id` (str): 标签页 ID

**返回:**
- `message`: 操作结果消息
- `tab_id`: 标签页 ID
- `recommend_team`: 推荐的采集方案
  - `requests`: 静态页面，无防护
  - `drissionpage_headless`: 动态页面或有 requests 防护
  - `drissionpage_head`: 有无头检测或复杂 WAF
- `raw_head_rate_difference`: requests 与有头浏览器压缩比差异
- `raw_headless_rate_difference`: requests 与无头浏览器压缩比差异
- `head_headless_rate_difference`: 有头与无头浏览器压缩比差异

## 📊 WAF 检测逻辑

### 判定规则

| 场景 | requests vs 有头 | requests vs 无头 | 有头 vs 无头 | 推荐方案 | 说明 |
|------|------------------|------------------|--------------|----------|------|
| 静态页面无防护 | < 40% | < 40% | < 40% | `requests` | 三种方式结果一致 |
| 动态页面 / requests 防护 | > 40% | > 40% | < 30% | `drissionpage_headless` | requests 拿不到正确结果 |
| 无头检测 / 复杂 WAF | < 15% | > 40% | > 40% | `drissionpage_head` | 必须使用有头浏览器 |
| 已知 WAF (Cookie) | - | - | - | `drissionpage_head` | 检测到瑞数/加速乐等 Cookie |
| 状态码检测 | 412/521 | - | - | `drissionpage_head` | 瑞数(412)/加速乐(521) |

### Cookie 特征库

当前支持识别的 WAF：
- **瑞数**: Cookie name 长度为 13，value 长度为 88
- **加速乐**: Cookie name 包含 `_jsl`

## 🏗️ 项目结构

```
Jarvis-mcp/
├── mcp_tools/           # MCP 工具模块
│   ├── __init__.py
│   ├── main.py         # 主入口，注册 MCP 工具
│   └── dp_tools.py     # DrissionPage 工具函数
├── tools/              # 核心工具模块
│   ├── __init__.py
│   ├── browser_manager.py  # 浏览器池管理（单例模式）
│   └── tools.py        # HTML 处理、WAF 检测等工具函数
├── dist/               # 打包文件
├── pyproject.toml      # 项目配置
└── README.md          # 项目文档
```

## 🔧 技术栈

- **[FastMCP](https://github.com/jlowin/fastmcp)**: MCP 服务器框架
- **[DrissionPage](https://github.com/g1879/DrissionPage)**: 浏览器控制库
- **[htmlmin](https://github.com/mankyd/htmlmin)**: HTML 压缩
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)**: HTML 解析
- **[curl_cffi](https://github.com/yifeikong/curl_cffi)**: HTTP 请求库

## 📝 使用方法

### teamNode mcp配置

```json
"JarvisNode": {
    "command": "uvx",
    "args": ["--python", "3.11", "--from", "Jarvis_Brain@latest", "jarvis-mcp"],
    "env": {
        "MCP_MODULES": "TeamNode-Dp",
        "BASE_CWD": os.getcwd(),
    }
},
```

### JarvisNode mcp配置

```json
"JarvisNode": {
    "command": "uvx",
    "args": ["--python", "3.11", "--from", "Jarvis_Brain@latest", "jarvis-mcp"],
    "env": {
        "MCP_MODULES": "TeamNode-Dp,JarvisNode",
        "BASE_CWD": os.getcwd(),
    }
},
```

## 🌟 应用场景

1. **网页爬虫**: 智能选择最优采集方案，提高爬取效率
2. **反爬虫分析**: 快速识别网站使用的 WAF 类型
3. **自动化测试**: 多浏览器实例并发测试
4. **数据采集**: 处理动态渲染、反爬虫网站
5. **安全研究**: 分析网站防护策略

## 📄 许可证

本项目采用 MIT 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/yourusername/jarvis-mcp/issues)
- 邮箱: your.email@example.com

---

<div align="center">
Made with ❤️ by Jarvis Team
</div>
