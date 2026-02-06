import requests
import re
import os
import time
import pdfplumber
import shutil
from playwright.sync_api import sync_playwright

def download_51fapiao(url, output_dir="downloads"):
    """
    下载 51发票 (51fapiao) 的发票。
    参考 docs/51fapiao_download_process.md
    
    :param url: 51发票分享链接
    :param output_dir: 保存目录
    :return: 成功返回 PDF 路径，失败返回 None
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 提取 dlj_id
    match = re.search(r'/dlj/v7/([a-zA-Z0-9]+)', url)
    if not match:
        print(f"无效的 51发票链接: {url}")
        return None
    
    dlj_id = match.group(1)
    filename = f"51fapiao_{dlj_id}.pdf"
    output_path = os.path.join(output_dir, filename)

    print(f"正在处理 51发票: {url}")
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # 如果直接返回 PDF
        if "%PDF" in response.text[:10]:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"下载成功 (直接返回): {output_path}")
            
            # 识别发票类型并移动到对应分类文件夹
            invoice_type = classify_invoice_type(output_path)
            print(f"发票类型识别结果: {invoice_type}")
            move_to_category_folder(output_path, invoice_type)
            
            return output_path

        # 否则解析 signatureString
        html_content = response.text
        sig_match = re.search(r'id="signatureString"\s+value="([^"]+)"', html_content)
        if not sig_match:
            print("未能提取到 signatureString")
            return None
        
        signature = sig_match.group(1)
        download_url = f"https://dlj.51fapiao.cn/dlj/v7/downloadFile/{dlj_id}?signatureString={signature}"
        
        headers["Referer"] = url
        pdf_response = session.get(download_url, headers=headers, stream=True, timeout=30)
        pdf_response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in pdf_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"下载成功 (构造 URL): {output_path}")
        
        # 识别发票类型并移动到对应分类文件夹
        invoice_type = classify_invoice_type(output_path)
        print(f"发票类型识别结果: {invoice_type}")
        move_to_category_folder(output_path, invoice_type)
        
        return output_path

    except Exception as e:
        print(f"51发票下载失败: {e}")
        return None

def download_nuonuo(url, output_dir="downloads"):
    """
    下载 诺诺网 (Nuonuo) 的发票。
    参考 docs/nuonuo_download_process.md
    
    :param url: 诺诺网交付页面链接
    :param output_dir: 保存目录
    :return: 成功返回 PDF 路径，失败返回 None
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"正在使用 Playwright 处理诺诺网发票: {url}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            page = context.new_page()

            # 用于保存截获的下载链接
            download_info = {"url": None}

            # 监听 window.open
            page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
            
            # 注入脚本拦截 window.open 并捕获下载链接
            page.add_init_script("""
                const originalOpen = window.open;
                window.open = function(url) {
                    if (url && (url.includes('download') || url.includes('sid='))) {
                        console.log('CAPTURED_URL:' + url);
                    }
                    return null; // 阻止打开新窗口
                };
            """)

            # 捕获控制台输出中的链接
            def handle_console(msg):
                if msg.text.startswith("CAPTURED_URL:"):
                    download_info["url"] = msg.text.replace("CAPTURED_URL:", "")

            page.on("console", handle_console)

            # 访问页面
            page.goto(url, wait_until="networkidle")
            
            # 等待"下载PDF"按钮出现并点击
            # 诺诺网的按钮通常包含"下载"字样
            try:
                # 尝试查找包含"下载"文本的按钮
                download_btn = page.wait_for_selector("text=下载", timeout=10000)
                if download_btn:
                    download_btn.click()
                    # 等待一段时间让 JS 执行
                    time.sleep(3)
            except Exception as e:
                print(f"未找到下载按钮或点击失败: {e}")

            if download_info["url"]:
                # 使用 requests 下载，带上 Referer
                real_url = download_info["url"]
                if real_url.startswith("/"):
                    # 如果是相对路径，补全域名
                    from urllib.parse import urljoin
                    real_url = urljoin(url, real_url)
                
                print(f"截获到真实下载地址: {real_url}")
                
                # 提取文件名
                filename = f"nuonuo_{int(time.time())}.pdf"
                output_path = os.path.join(output_dir, filename)

                session = requests.Session()
                headers = {
                    "Referer": url,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                resp = session.get(real_url, headers=headers, stream=True, timeout=30)
                resp.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"诺诺网发票下载成功: {output_path}")
                
                # 识别发票类型并移动到对应分类文件夹
                invoice_type = classify_invoice_type(output_path)
                print(f"发票类型识别结果: {invoice_type}")
                move_to_category_folder(output_path, invoice_type)
                
                browser.close()
                return output_path
            else:
                print("未能截获诺诺网下载链接")
            
            browser.close()
            return None

    except Exception as e:
        print(f"诺诺网下载失败: {e}")
        return None


def classify_invoice_type(pdf_path):
    """
    识别发票类型：滴滴车票、火车票、餐费或其他
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # 检查是否包含滴滴相关关键词
        didi_keywords = ['滴滴', '滴滴出行', '快车', '专车', '出租车', '网约车', '行程']
        train_keywords = ['铁路', '火车', '高铁', '动车', '12306', '客票', '乘车']
        food_keywords = ['餐饮', '餐费', '饭费', '饮食', '餐厅', '酒楼', '饭店', '食堂', '茶楼', '茶饮', '咖啡', '菜品', '食品']

        text_lower = text.lower()
        
        didi_count = sum(1 for keyword in didi_keywords if keyword in text_lower)
        train_count = sum(1 for keyword in train_keywords if keyword in text_lower)
        food_count = sum(1 for keyword in food_keywords if keyword in text_lower)
        
        # 确定最大计数对应的类别
        max_count = max(didi_count, train_count, food_count)
        
        if max_count == 0:
            return "其他发票"  # 如果没有匹配任何关键词
        
        if didi_count == max_count:
            return "滴滴车票"
        elif train_count == max_count:
            return "火车票"
        elif food_count == max_count:
            return "餐费发票"
        else:
            return "其他发票"
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
        # 找到项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        target_dir = os.path.join(project_root, "downloads", category)
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