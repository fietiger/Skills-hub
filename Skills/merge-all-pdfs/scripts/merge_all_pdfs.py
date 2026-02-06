from pypdf import PdfReader, PdfWriter
import os
import sys

def merge_pdfs(pdf_list, output_filename):
    """
    合并PDF文件列表到输出文件
    """
    pdf_writer = PdfWriter()

    for pdf_file in pdf_list:
        if not os.path.exists(pdf_file):
            print(f"警告: 文件不存在 - {pdf_file}")
            continue
            
        try:
            pdf_reader = PdfReader(pdf_file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                pdf_writer.add_page(page)
            print(f"已添加: {os.path.basename(pdf_file)}")
        except Exception as e:
            print(f"错误: 无法处理文件 {pdf_file} - {str(e)}")

    with open(output_filename, 'wb') as output_pdf:
        pdf_writer.write(output_pdf)

def merge_pdfs_from_directory(directory, output_filename, specific_pdfs=None):
    """
    从指定目录合并PDF文件，可以选择性地包含特定PDF文件
    """
    pdfs_to_merge = []

    # 如果提供了特定的PDF列表，首先添加它们
    if specific_pdfs:
        for pdf in specific_pdfs:
            if os.path.exists(pdf):
                pdfs_to_merge.append(pdf)
            else:
                print(f"警告: 指定的PDF文件不存在 - {pdf}")

    # 然后添加目录中的所有PDF文件
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                # 避免重复添加已经在specific_pdfs中的文件
                if specific_pdfs and pdf_path in specific_pdfs:
                    continue
                pdfs_to_merge.append(pdf_path)

    # 按字母顺序排序以确保一致性
    pdfs_to_merge = sorted(pdfs_to_merge)

    print("要合并的PDF文件:")
    for pdf in pdfs_to_merge:
        print(f"  - {os.path.basename(pdf)}")

    # 合并PDF
    merge_pdfs(pdfs_to_merge, output_filename)
    print(f"\n合并完成！输出文件: {output_filename}")
    return pdfs_to_merge

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python merge_all_pdfs.py <输出文件名> <输入目录> [PDF文件1] [PDF文件2] ...")
        print("示例: python merge_all_pdfs.py 费用报销综合.pdf 发票汇总 费用报销单_已填写.pdf 费用清单.pdf")
        sys.exit(1)

    output_filename = sys.argv[1]
    input_directory = sys.argv[2]
    specific_pdfs = sys.argv[3:]  # 从第4个参数开始都是特定的PDF文件

    print(f"输出文件: {output_filename}")
    print(f"输入目录: {input_directory}")
    if specific_pdfs:
        print(f"特定PDF文件: {specific_pdfs}")

    merge_pdfs_from_directory(input_directory, output_filename, specific_pdfs)