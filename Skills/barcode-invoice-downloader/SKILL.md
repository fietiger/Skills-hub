---
name: barcode-invoice-downloader
description: 通过识别“发票二维码”目录中的图片，解析出发票下载链接，并使用 Playwright 模拟浏览器自动下载 PDF 发票。
---

# 发票二维码识别下载技能

此技能专门用于处理包含发票二维码的图片。它能够自动识别图片中的二维码，并针对江苏税务等需要动态渲染和 JS 交互的网站进行自动化下载。

## 使用场景

- 手头有发票二维码图片（如手机截图或导出的图片），需要批量下载对应的 PDF 电子发票。
- 发票下载页面具有 WAF 防护或复杂的 JS 渲染（如单页面应用 SPA），普通爬虫无法直接获取。

## 核心功能

1. **二维码解析**：
   - 使用 `opencv` 和 `pyzbar` 识别图片。
   - 特别处理了中文路径兼容性问题。
2. **自动化下载引擎**：
   - **Playwright 驱动**：模拟真实用户行为，处理动态加载。
   - **流量拦截 (Hook)**：通过注入 JS 拦截 `window.open` 和 `location.assign`，捕获真实的 PDF 流地址。
   - **指纹伪装**：移除 `webdriver` 标记，设置真实 `User-Agent`，规避反爬校验。
3. **混合下载模式**：
   - 优先监听浏览器的 `download` 事件。
   - 若自动下载未触发，则使用带 Session/Cookie 的 `requests` 进行二次尝试。

## 工作流程

1. **扫描目录**：扫描项目根目录下 `发票二维码/` 文件夹中的所有图片。
2. **解析 URL**：对每张图片进行解码，获取发票查验/下载 URL。
3. **浏览器导航**：启动 Playwright 访问该 URL。
4. **触发下载**：自动寻找并点击页面上的“下载”、“PDF”等关键字按钮。
5. **保存文件**：将获取到的 PDF 文件保存至 `downloads/` 目录。

## 使用指南

在项目根目录下运行以下命令：

```powershell
python skills/barcode-invoice-downloader/scripts/download_by_barcode.py
```

### 依赖项

- `opencv-python`: 用于图像读取。
- `pyzbar`: 用于二维码解码。
- `playwright`: 用于浏览器自动化交互。
- `requests`: 用于辅助下载。

### 目录结构要求

- **输入**：项目根目录下的 `发票二维码/` 文件夹。
- **输出**：项目根目录下的 `downloads/` 文件夹。
