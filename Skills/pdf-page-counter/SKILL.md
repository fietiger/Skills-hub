---
name: "pdf-page-counter"
description: "计算指定文件或目录中所有 PDF 文件的总页数。在需要汇总发票附件页数或统计 PDF 规模时调用。"
---

# PDF 页数汇总器 (PDF Page Counter)

此技能用于递归统计一个或多个路径下所有 PDF 文件的总页数。

## 使用场景

- **报销汇总**：统计发票汇总文件夹及其他附件（如费用清单）的总页数，用于填写报销单。
- **文档管理**：快速查看多个 PDF 文档的规模。

## 核心功能

1. **多路径支持**：可以同时传入多个文件路径或目录路径。
2. **递归统计**：自动遍历目录及其子目录下的所有 `.pdf` 文件。
3. **明细输出**：显示每个文件的页数以及最终的总合计。

## 使用方法

在终端运行以下命令：

```powershell
python .trae/skills/pdf-page-counter/scripts/count_pdf_pages.py <路径1> [路径2] ...
```

### 示例

统计“发票汇总”文件夹和“费用清单.pdf”的总页数：

```powershell
python .trae/skills/pdf-page-counter/scripts/count_pdf_pages.py "发票汇总" "费用清单.pdf"
```

## 输出格式

脚本将输出一个简单的表格，列出所有扫描到的 PDF 文件及其页数，最后给出总计。
