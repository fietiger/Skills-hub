import os
import pandas as pd
import pdfplumber
from pathlib import Path
import re
from pyzbar.pyzbar import decode
from PIL import Image as PILImage
import io

def extract_general_invoice_info(pdf_path):
    """
    通用发票信息提取函数，模仿滴滴发票提取格式
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # 初始化返回字典
        invoice_info = {
            '文件名': Path(pdf_path).name,
            '开票日期': '',
            '金额': '',
            '购买方名称': '',
            '购买方识别号': '',
            '销售方名称': '',
            '销售方识别号': ''
        }
        
        # 尝试从二维码提取信息
        try:
            # 首先尝试从整个页面图片识别二维码
            for page in pdf.pages:
                # 转换整个页面为图片
                page_image = page.to_image(resolution=150)
                
                # 尝试识别整个页面的二维码
                decoded = decode(page_image.original)
                if decoded:
                    for obj in decoded:
                        if obj.type == 'QRCODE':
                            # 解析二维码数据
                            qr_data = obj.data.decode('utf-8')
                            print(f"二维码数据: {qr_data}")
                            # 格式: 01,10,发票代码,发票号码,金额,日期,校验码,机器编号
                            parts = qr_data.split(',')
                            print(f"分割后的部分: {parts}")
                            if len(parts) >= 6:
                                invoice_info['开票日期'] = parts[5]  # 日期在第6位(索引5)
                                print(f"从二维码提取到日期: {parts[5]}")
                                break
                # 如果已提取到日期，跳出循环
                if invoice_info['开票日期']:
                    break
        except Exception as e:
            print(f"二维码提取失败: {e}")
        
        # 如果二维码没有提取到日期，再尝试从文本提取
        if not invoice_info['开票日期']:
            # 匹配 YYYY年MM月DD日 或 YYYY/MM/DD 或 YYYY-MM-DD 格式
            date_patterns = [
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
                r'开票日期[:：]\s*([^\s]{8,20})'
            ]
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    invoice_info['开票日期'] = match.group(1)
                    break
        
        # 尝试提取金额
        # 按优先级排序：价税合计 > 合计 > 其他金额
        # 首先查找价税合计（最能代表发票总额）
        tax_total_patterns = [
            r'价税合计\(大写\)[^¥￥]*\(小写\)[¥￥\s]*(\d+\.?\d*)',
            r'价税合计[（\(][^¥￥\)]*\)[¥￥\s]*(\d+\.?\d*)',  # 修改：匹配 (大写) (小写) 格式
            r'价税合计.{0,10}[：:]\s*[¥￥]?\s*(\d+\.?\d*)',
            r'大写.{0,10}小写[¥￥\s]*(\d+\.?\d*)',  # 匹配 大写...小写¥金额 格式
            r'大写.{0,30}¥\s*(\d+\.?\d*)',  # 匹配 大写...金额 格式
            r'[壹贰叁肆伍陆柒捌玖拾佰仟万亿元圆角分零整]{2,}[^\d]*¥\s*(\d+\.?\d*)'  # 匹配大写金额后跟符号
        ]
        
        for pattern in tax_total_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 取最大的匹配值
                amounts = []
                for x in matches:
                    try:
                        val = float(x)
                        if val > 0:
                            amounts.append(val)
                    except ValueError:
                        continue
                if amounts:
                    invoice_info['金额'] = max(amounts)
                    break
        
        # 如果没找到价税合计，再查找其他合计
        if not invoice_info['金额']:
            subtotal_patterns = [
                r'[合]?计.{0,5}[：:]\s*[¥￥]?\s*(\d+\.?\d*)',
                r'金额.{0,5}[：:]\s*[¥￥]?\s*(\d+\.?\d*)',
                r'小计.{0,5}[：:]\s*[¥￥]?\s*(\d+\.?\d*)',
                r'[¥￥]\s*(\d+\.?\d*)',
                r'(\d+\.?\d{2})'  # 匹配标准货币格式
            ]
            
            for pattern in subtotal_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    amounts = []
                    for x in matches:
                        try:
                            val = float(x)
                            if val > 0:
                                amounts.append(val)
                        except ValueError:
                            continue
                    if amounts:
                        invoice_info['金额'] = max(amounts)
                        break
        
        # 尝试提取购买方信息
        buyer_patterns = [
            r'购买方.{0,50}名称[：:]\s*([^\n\r]{10,50})',
            r'购买方.{0,50}名[：:]\s*([^\n\r]{10,50})',
            r'付款方.{0,50}[：:]\s*([^\n\r]{10,50})'
        ]
        for pattern in buyer_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                buyer_name = match.group(1).strip()
                # 清理掉可能包含的纳税人识别号部分
                buyer_name = re.sub(r'纳税人识别号.{0,5}[：:]\s*[^\s]+', '', buyer_name).strip()
                invoice_info['购买方名称'] = buyer_name
                break
        
        # 尝试提取购买方识别号
        buyer_tax_patterns = [
            r'购买方.{0,100}纳税人识别号[：:]\s*([^\s\n\r]{10,30})',
            r'付款方.{0,100}纳税人识别号[：:]\s*([^\s\n\r]{10,30})',
            r'纳税人识别号[：:]\s*([^\s\n\r]{10,30})'
        ]
        for pattern in buyer_tax_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                invoice_info['购买方识别号'] = match.group(1).strip()
                break
        
        # 尝试提取销售方信息
        seller_patterns = [
            r'销售方.{0,50}名称[：:]\s*([^\n\r]{10,50})',
            r'销售方.{0,50}名[：:]\s*([^\n\r]{10,50})',
            r'收款方.{0,50}[：:]\s*([^\n\r]{10,50})'
        ]
        for pattern in seller_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                seller_name = match.group(1).strip()
                # 清理掉可能包含的纳税人识别号部分
                seller_name = re.sub(r'纳税人识别号.{0,5}[：:]\s*[^\s]+', '', seller_name).strip()
                invoice_info['销售方名称'] = seller_name
                break
        
        # 尝试提取销售方识别号
        seller_tax_patterns = [
            r'销售方.{0,100}纳税人识别号[：:]\s*([^\s\n\r]{10,30})',
            r'收款方.{0,100}纳税人识别号[：:]\s*([^\s\n\r]{10,30})'
        ]
        for pattern in seller_tax_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                invoice_info['销售方识别号'] = match.group(1).strip()
                break
        
        return invoice_info
        
    except Exception as e:
        print(f"提取发票信息时出错 {pdf_path}: {e}")
        return {
            '文件名': Path(pdf_path).name,
            '开票日期': '提取失败',
            '金额': '',
            '购买方名称': '',
            '购买方识别号': '',
            '销售方名称': '',
            '销售方识别号': ''
        }


def extract_invoices_from_directory(input_dir, output_file):
    """
    从指定目录提取所有PDF发票的信息
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"目录不存在: {input_dir}")
        return
    
    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        print(f"在 {input_dir} 中未找到PDF文件")
        return
    
    print(f"找到 {len(pdf_files)} 个PDF文件")
    
    extracted_data = []
    for pdf_file in pdf_files:
        print(f"正在处理: {pdf_file.name}")
        invoice_info = extract_general_invoice_info(pdf_file)
        extracted_data.append(invoice_info)
    
    # 创建DataFrame并保存到Excel
    df = pd.DataFrame(extracted_data)
    
    # 设置列顺序
    columns_order = ['文件名', '开票日期', '金额', '购买方名称', '购买方识别号', '销售方名称', '销售方识别号']
    df = df.reindex(columns=columns_order)
    
    # 保存到Excel
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"数据已保存到: {output_file}")
    print(f"共处理 {len(extracted_data)} 条记录")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("用法: python extract_general_invoices.py <输入目录> <输出文件>")
        print("示例: python extract_general_invoices.py 住宿发票 住宿发票信息汇总.xlsx")
    else:
        input_dir = sys.argv[1]
        output_file = sys.argv[2]
        extract_invoices_from_directory(input_dir, output_file)
