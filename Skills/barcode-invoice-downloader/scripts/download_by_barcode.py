import cv2
import numpy as np
from pyzbar.pyzbar import decode
import os
from playwright.sync_api import sync_playwright
import time
import requests

def decode_qr(file_path):
    """
    解码二维码图片，支持中文路径
    """
    print(f"正在解码: {file_path}")
    try:
        # 使用 numpy 读取以支持中文路径
        img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)
        if img is None:
            print(f"错误: 无法读取图片 {file_path}")
            return None
        
        decoded_objects = decode(img)
        if not decoded_objects:
            print(f"未在图片中找到二维码: {file_path}")
            return None
        
        data = decoded_objects[0].data.decode('utf-8')
        print(f"解码成功: {data}")
        return data
    except Exception as e:
        print(f"解码过程中出错: {e}")
        return None

def download_invoice(url, output_dir="downloads"):
    """
    使用 Playwright 导航并下载发票
    """
    if not os.path.isabs(output_dir):
        # 确保 output_dir 相对于项目根目录
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        output_dir = os.path.join(project_root, output_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with sync_playwright() as p:
        # 启动浏览器，伪装指纹
        browser = p.chromium.launch(headless=True) # 默认使用无头模式
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        
        page = context.new_page()
        
        # 注入 Hook 拦截 window.open 和 location.assign
        page.add_init_script("""
            window.open = (url) => { console.log("CAPTURED_URL:" + url); window.captured_pdf_url = url; return null; };
            window.location.assign = (url) => { console.log("CAPTURED_URL:" + url); window.captured_pdf_url = url; };
            // 移除 webdriver 标记
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        captured_url = [None]

        # 监听控制台输出以获取捕获的 URL
        def handle_console(msg):
            if "CAPTURED_URL:" in msg.text:
                url = msg.text.split("CAPTURED_URL:")[1]
                captured_url[0] = url
                print(f"捕获到下载地址: {url}")

        page.on("console", handle_console)
        
        # 监听下载事件
        def handle_download(download):
            path = os.path.join(output_dir, download.suggested_filename)
            download.save_as(path)
            print(f"文件已下载至: {path}")
            captured_url[0] = path # 标记为已下载

        page.on("download", handle_download)

        print(f"正在访问: {url}")
        try:
            page.goto(url, wait_until="networkidle")
            
            # 某些页面可能需要点击按钮才能触发下载/跳转
            # 寻找常见的“预览”、“下载”、“查看PDF”按钮
            buttons = page.query_selector_all("button, a.btn, .download-link")
            for btn in buttons:
                text = btn.inner_text().lower()
                if any(kw in text for kw in ["pdf", "下载", "查看", "预览", "download", "view"]):
                    print(f"尝试点击按钮: {text}")
                    btn.click()
                    page.wait_for_timeout(3000)
                    if captured_url[0]: break

            # 如果捕获到了 URL 但没有触发自动下载，尝试使用 requests 下载
            if captured_url[0] and captured_url[0].startswith("http"):
                pdf_url = captured_url[0]
                print(f"尝试手动下载 PDF: {pdf_url}")
                
                # 获取 cookies
                cookies = context.cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies}
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": url
                }
                
                response = requests.get(pdf_url, headers=headers, cookies=cookie_dict, stream=True)
                if response.status_code == 200:
                    filename = pdf_url.split("/")[-1].split("?")[0]
                    if not filename.endswith(".pdf"):
                        filename = "invoice_" + str(int(time.time())) + ".pdf"
                    
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"手动下载成功: {filepath}")
                else:
                    print(f"手动下载失败，状态码: {response.status_code}")

            # 等待一段时间确保下载完成
            time.sleep(5)
        except Exception as e:
            print(f"访问或下载过程中出错: {e}")
        finally:
            browser.close()

def main():
    # 确定项目根目录
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    qr_dir = os.path.join(project_root, "发票二维码")
    
    if not os.path.exists(qr_dir):
        print(f"错误: 目录 {qr_dir} 不存在")
        return

    files = [f for f in os.listdir(qr_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
    if not files:
        print(f"在 {qr_dir} 中未找到图片文件")
        return

    for file in files:
        file_path = os.path.join(qr_dir, file)
        qr_data = decode_qr(file_path)
        if qr_data:
            download_invoice(qr_data)

if __name__ == "__main__":
    main()
