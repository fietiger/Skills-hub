import imaplib
import email
from email.header import decode_header
import os
import re
from invoice_downloader import download_51fapiao, download_nuonuo

# 邮箱配置信息
IMAP_SERVER = "imap.163.com"
IMAP_PORT = 993
EMAIL_ACCOUNT = "17520498972@163.com"
EMAIL_AUTH_CODE = "URjbzGLR7CuPRr69"

def clean_filename(filename):
    """
    清理文件名中的非法字符
    
    :param filename: 原始文件名
    :return: 清理后的文件名
    """
    return "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_')).rstrip()

def extract_links(html_content):
    """
    从 HTML 中提取链接
    
    :param html_content: HTML 内容
    :return: 链接列表
    """
    # 查找所有 href 链接 (支持双引号和单引号)
    links = re.findall(r'href=["\']([^"\']+)["\']', html_content)
    # 同时也查找文本中的普通链接
    text_links = re.findall(r'(https?://[^\s<>"\']+)', html_content)
    return list(set(links + text_links))

def download_emails():
    """
    主函数：连接邮箱、处理邮件、下载发票并清理广告邮件
    """
    # 获取项目根目录 (假设脚本在 skills/email-invoice-downloader/scripts 下)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    # 创建保存目录 (使用绝对路径)
    html_output_dir = os.path.join(base_dir, "emails_html")
    pdf_output_dir = os.path.join(base_dir, "downloads")
    
    for d in [html_output_dir, pdf_output_dir]:
        if not os.path.exists(d):
            os.makedirs(d)

    try:
        # 连接服务器
        print(f"正在连接到 {IMAP_SERVER}...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)

        # 163 邮箱特殊要求：在 SELECT 前发送 ID 标识
        print("发送 ID 标识...")
        imaplib.Commands['ID'] = ('NONAUTH', 'AUTH', 'SELECTED')
        mail._command('ID', '("name" "python-imap" "version" "1.0.0")')

        # 登录
        print(f"正在登录 {EMAIL_ACCOUNT}...")
        mail.login(EMAIL_ACCOUNT, EMAIL_AUTH_CODE)

        # 选择收件箱
        mail.select("INBOX")

        # 搜索邮件 (未读邮件优先，如果没有未读则处理最近的)
        status, messages = mail.search(None, 'UNSEEN')
        if status == 'OK' and messages[0]:
            mail_ids = messages[0].split()
            print(f"找到 {len(mail_ids)} 封未读邮件")
        else:
            print("没有找到未读邮件，正在获取最近的 20 封邮件...")
            status, messages = mail.search(None, 'ALL')
            if status == 'OK':
                mail_ids = messages[0].split()
                mail_ids = mail_ids[-20:] # 减少处理数量以提高速度
            else:
                print("搜索邮件失败")
                return
        
        print(f"准备处理 {len(mail_ids)} 封邮件")

        # 遍历邮件
        for mail_id in mail_ids:
            status, data = mail.fetch(mail_id, '(RFC822)')
            if status != 'OK':
                print(f"获取邮件 {mail_id} 失败")
                continue

            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            # 解析邮件主题
            subject_parts = decode_header(msg["Subject"])
            subject = ""
            for part, encoding in subject_parts:
                if isinstance(part, bytes):
                    subject += part.decode(encoding if encoding else "utf-8", errors="ignore")
                else:
                    subject += part
            
            # 获取发件人
            from_header = str(msg.get("From"))
            
            # 1. 自动删除广告邮件 (根据 basicinfo.md 规则)
            if "member@service.netease.com" in from_header.lower():
                print(f"\n[广告] 正在删除广告邮件: {subject} (From: {from_header})")
                mail.store(mail_id, '+FLAGS', '\\Deleted')
                continue

            # 过滤发票相关邮件 (为了避免误删非广告但非发票的邮件，我们这里仅处理感兴趣的)
            if "发票" not in subject and "行程单" not in subject and "电子凭证" not in subject:
                continue

            print(f"\n--- 正在处理邮件: {subject} ---")

            has_pdf_attachment = False
            html_content = ""
            attachments = []

            # 1. 遍历邮件部分，寻找 PDF 附件和 HTML 内容
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                filename = part.get_filename()

                if filename:
                    # 解码文件名
                    decoded_filename_parts = decode_header(filename)
                    decoded_filename = ""
                    for f_part, f_encoding in decoded_filename_parts:
                        if isinstance(f_part, bytes):
                            decoded_filename += f_part.decode(f_encoding if f_encoding else "utf-8", errors="ignore")
                        else:
                            decoded_filename += f_part
                    
                    if decoded_filename.lower().endswith(".pdf"):
                        # 下载 PDF 附件
                        safe_name = clean_filename(decoded_filename)
                        pdf_path = os.path.join(pdf_output_dir, safe_name)
                        with open(pdf_path, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        print(f"已下载 PDF 附件: {safe_name}")
                        has_pdf_attachment = True
                
                # 提取 HTML 内容
                if content_type == "text/html" and "attachment" not in content_disposition:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    html_content = payload.decode(charset, errors='ignore')

            # 2. 如果没有 PDF 附件，将该邮件保存为 HTML (根据用户要求)
            if not has_pdf_attachment:
                if html_content:
                    safe_subject = clean_filename(subject) or f"email_{mail_id.decode()}"
                    html_file_path = os.path.join(html_output_dir, f"{safe_subject}.html")
                    with open(html_file_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    print(f"附件中无 PDF，已保存邮件原文为 HTML: {os.path.basename(html_file_path)}")
                
                # 3. 尝试从链接下载 (参考 51fapiao 和 nuonuo 流程)
                if html_content:
                    raw_links = extract_links(html_content)
                    processed_links = set()
                    
                    # 预处理链接：提取真实地址并去重
                    for link in raw_links:
                        # 诺诺网二维码转换
                        if "nnfp.jss.com.cn" in link and "getEwmImg.do?content=" in link:
                            match = re.search(r'content=(https?://[^\s&]+)', link)
                            if match: link = match.group(1)
                        processed_links.add(link)
                    
                    # 记录该邮件是否已成功下载发票，避免重复处理同一邮件中的多个相同发票链接
                    download_success = False
                    
                    for link in processed_links:
                        # 处理 51发票
                        if "dlj.51fapiao.cn" in link:
                            print(f"检测到 51发票链接，尝试下载: {link}")
                            if download_51fapiao(link, pdf_output_dir):
                                download_success = True
                        
                        # 处理 诺诺网
                        elif "nnfp.jss.com.cn" in link:
                            print(f"检测到 诺诺网链接，尝试下载: {link}")
                            if download_nuonuo(link, pdf_output_dir):
                                download_success = True
                        
                        # 如果已成功下载（对于通常一封邮件一个发票的情况），可以考虑 break
                        # 但为了稳妥，如果确实有多个不同链接，去掉 break。
                        # 这里通过 set(processed_links) 已经解决了相同链接的问题。
                        if download_success:
                            # 如果你确定一封邮件只应该下载一个 PDF，可以取消下面 break 的注释
                            # break 
                            pass
        
        # 永久删除标记为 Deleted 的邮件
        mail.expunge()
        # 登出
        mail.logout()
        print("\n所有邮件处理完成")

    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    download_emails()
