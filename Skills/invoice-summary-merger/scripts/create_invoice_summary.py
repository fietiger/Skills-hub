import os
import shutil
import pdfplumber
from pathlib import Path

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
        
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['住宿', '酒店', '旅馆', '客房']):
            return "住宿发票"
        if any(kw in text_lower for kw in ['滴滴', '快车', '专车', '网约车']):
            return "滴滴车票"
        if any(kw in text_lower for kw in ['铁路', '火车', '高铁', '12306', '客票']):
            return "火车票"
        if any(kw in text_lower for kw in ['餐饮', '餐费', '饮食', '食品']):
            return "餐费发票"
        return "其他发票"
    except:
        return "其他发票"

def create_invoice_summary():
    """
    将所有不同来源的发票汇总到统一的汇总文件夹中，并按分类存放
    """
    # 项目根目录
    project_root = Path.cwd()
    
    # 定义源目录（各种发票分类目录）
    # 包括项目根目录下的住宿发票、已有发票和其他在.trae/downloads下的分类
    source_dirs = [
        project_root / "住宿发票",  # 从二维码下载的住宿发票
        project_root / "已有发票",  # 用户特别提到的已有发票
        project_root / ".trae" / "downloads" / "住宿发票", 
        project_root / ".trae" / "downloads" / "滴滴车票", 
        project_root / ".trae" / "downloads" / "火车票",
        project_root / ".trae" / "downloads" / "餐费发票",
        project_root / ".trae" / "downloads" / "其他发票",
    ]
    
    # 定义汇总目录
    summary_base_dir = project_root / "发票汇总"
    
    # 创建汇总目录结构
    summary_categories = ["住宿发票", "滴滴车票", "火车票", "餐费发票", "其他发票"]
    for category in summary_categories:
        category_dir = summary_base_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        print(f"创建汇总目录: {category_dir}")
    
    # 统计信息
    total_moved = 0
    
    # 遍历每个源目录
    for src_dir in source_dirs:
        if src_dir.exists() and src_dir.is_dir():
            category_name = src_dir.name
            
            # 如果是“已有发票”，我们需要对其中的文件进行分类
            is_generic_source = category_name == "已有发票"
            
            print(f"\n正在处理 {src_dir}")
            
            # 遍历源目录中的所有PDF文件
            for pdf_file in src_dir.glob("*.pdf"):
                # 确定目标分类
                if is_generic_source:
                    target_category = classify_invoice_type(pdf_file)
                else:
                    target_category = category_name if category_name in summary_categories else "其他发票"
                
                dest_dir = summary_base_dir / target_category
                dest_file = dest_dir / pdf_file.name
                
                # 复制文件到汇总目录（直接覆盖同名文件，避免产生重复后缀）
                shutil.copy2(pdf_file, dest_file)
                print(f"  已复制: {pdf_file.name} -> {dest_file.name} (分类: {target_category})")
                total_moved += 1
    
    print(f"\n汇总完成！总共处理了 {total_moved} 个发票文件")
    print(f"汇总目录位置: {summary_base_dir}")

if __name__ == "__main__":
    create_invoice_summary()