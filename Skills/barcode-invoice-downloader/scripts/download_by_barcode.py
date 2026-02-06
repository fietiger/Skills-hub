import cv2
import numpy as np
from pyzbar.pyzbar import decode
import os
from playwright.sync_api import sync_playwright
import time
import requests
import pdfplumber
import shutil

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

def classify_invoice_type(pdf_path):
    """
    识别发票类型：住宿或餐饮
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # 检查是否包含住宿相关关键词
        accommodation_keywords = ['住宿', '宾馆', '酒店', '旅馆', '客栈', '民宿', '度假村', '会所', '公寓']
        food_keywords = ['餐饮', '餐费', '饭费', '饮食', '餐厅', '酒楼', '饭店', '食堂', '茶楼', '茶饮', '咖啡']

        text_lower = text.lower()
        
        accommodation_count = sum(1 for keyword in accommodation_keywords if keyword in text_lower)
        food_count = sum(1 for keyword in food_keywords if keyword in text_lower)
        
        if accommodation_count > food_count:
            return "住宿发票"
        elif food_count > accommodation_count:
            return "餐饮发票"
        else:
            # 如果无法明确分类，尝试进一步分析
            # 检查是否包含住宿特有的关键词
            accommodation_specific = ['住宿服务', '房费', '客房', '钟点房', '套房', '标间', '单间']
            food_specific = ['餐饮服务', '菜品', '酒水', '饮料', '食品', '火锅', '烧烤', '自助餐']
            
            accommodation_specific_count = sum(1 for keyword in accommodation_specific if keyword in text_lower)
            food_specific_count = sum(1 for keyword in food_specific if keyword in text_lower)
            
            if accommodation_specific_count > food_specific_count:
                return "住宿发票"
            elif food_specific_count > accommodation_specific_count:
                return "餐饮发票"
            else:
                return "其他发票"  # 如果仍然无法分类，则归为其他
    except Exception as e:
        print(f"识别发票类型时出错: {e}")
        return "其他发票"


def move_to_category_folder(file_path, category):
    """
    将发票移动到对应的分类文件夹
    """
    try:
        # 获取原始文件名
        filename = os.path.basename(file_path)
        
        # 创建目标文件夹路径
        target_dir = os.path.join(os.path.dirname(file_path), category)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        # 创建目标文件路径
        target_path = os.path.join(target_dir, filename)
        
        # 移动文件
        shutil.move(file_path, target_path)
        print(f"文件已移动到: {target_path}")
        
        return target_path
    except Exception as e:
        print(f"移动文件时出错: {e}")
        return file_path


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
            
            # 如果成功下载了PDF文件，进行分类
            if captured_url[0] and os.path.isfile(captured_url[0]) and captured_url[0].endswith('.pdf'):
                downloaded_file_path = captured_url[0]
                print(f"正在识别发票类型: {downloaded_file_path}")
                
                # 识别发票类型
                invoice_type = classify_invoice_type(downloaded_file_path)
                print(f"发票类型识别结果: {invoice_type}")
                
                # 移动到对应分类文件夹
                move_to_category_folder(downloaded_file_path, invoice_type)
        except Exception as e:
            print(f"访问或下载过程中出错: {e}")
        finally:
            browser.close()

def main():
    # 确定项目根目录（使用当前工作目录）
    project_root = os.getcwd()
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
