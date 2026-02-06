import os
import sys
from pypdf import PdfReader

def count_pages(target_paths):
    """
    计算给定路径列表中的 PDF 总页数。
    路径可以是文件或目录。如果是目录，将递归遍历其中的所有 PDF。
    """
    total_pages = 0
    detailed_info = []

    for path in target_paths:
        if not os.path.exists(path):
            print(f"警告: 路径不存在 - {path}")
            continue

        if os.path.isfile(path):
            if path.lower().endswith('.pdf'):
                try:
                    reader = PdfReader(path)
                    pages = len(reader.pages)
                    total_pages += pages
                    detailed_info.append((path, pages))
                except Exception as e:
                    print(f"错误: 无法读取文件 {path} - {e}")
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        try:
                            reader = PdfReader(file_path)
                            pages = len(reader.pages)
                            total_pages += pages
                            detailed_info.append((file_path, pages))
                        except Exception as e:
                            print(f"错误: 无法读取文件 {file_path} - {e}")
    
    return total_pages, detailed_info

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python count_pdf_pages.py <路径1> [路径2] ...")
        print("路径可以是 PDF 文件或包含 PDF 的文件夹。")
        sys.exit(1)

    targets = sys.argv[1:]
    total, details = count_pages(targets)

    print("-" * 40)
    print(f"{'文件名':<30} | {'页数':<5}")
    print("-" * 40)
    for path, pages in details:
        print(f"{os.path.basename(path):<30} | {pages:<5}")
    print("-" * 40)
    print(f"总计 PDF 页数: {total}")
