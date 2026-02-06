import win32com.client
import os
import sys

def excel_to_pdf_win32(excel_path, pdf_path):
    """
    使用Win32COM将Excel转换为PDF，有更好的中文支持
    """
    # 检查文件是否存在
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"找不到Excel文件: {excel_path}")
    
    # 创建Excel应用对象
    excel_app = win32com.client.Dispatch("Excel.Application")
    
    try:
        # 设置Excel不可见
        excel_app.Visible = False
        excel_app.DisplayAlerts = False  # 关闭警告
        
        # 打开工作簿
        workbook = excel_app.Workbooks.Open(os.path.abspath(excel_path))
        
        # 导出为PDF
        # xlTypePDF = 0
        workbook.ExportAsFixedFormat(0, os.path.abspath(pdf_path))
        
        print(f"Excel文件已成功转换为PDF（使用Win32COM）: {pdf_path}")
        
    except Exception as e:
        print(f"转换失败: {str(e)}")
        raise
    finally:
        # 关闭工作簿和Excel应用
        try:
            workbook.Close()
        except:
            pass
        
        try:
            excel_app.Quit()
        except:
            pass

def count_pdf_pages(pdf_path):
    """
    计算PDF文件的页数
    """
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    return len(reader.pages)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python convert_xlsx_to_pdf.py <excel_file> <pdf_file>")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    pdf_file = sys.argv[2]
    
    if not os.path.exists(excel_file):
        print(f"错误: 找不到Excel文件 {excel_file}")
        sys.exit(1)
    
    try:
        # 使用Win32COM转换Excel到PDF
        excel_to_pdf_win32(excel_file, pdf_file)
        
        # 计算PDF页数
        page_count = count_pdf_pages(pdf_file)
        print(f"PDF文件页数: {page_count}")
    except Exception as e:
        print(f"转换失败: {str(e)}")
        sys.exit(1)