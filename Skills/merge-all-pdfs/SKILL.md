---
name: "merge-all-pdfs"
description: "合并多个PDF文件到一个PDF文件中。当需要将多个PDF文档合并为一个综合文档时调用。"
---

# Merge All PDFs

此技能用于将多个PDF文件合并成一个PDF文件。

## 功能

- 合并指定目录中的所有PDF文件
- 可选择性地首先合并特定的PDF文件
- 按照指定顺序合并PDF文档
- 生成单一的综合PDF文件

## 使用场景

当需要将多个PDF文档（如报销单、费用清单、发票等）合并为一个综合文档时使用此技能。

## 参数

- `output_filename`: 输出的合并PDF文件名
- `input_directory`: 包含要合并PDF文件的目录
- `[specific_pdfs...]`: 可选参数，要首先合并的特定PDF文件列表

## 示例

```python
python merge_all_pdfs.py 费用报销综合.pdf 发票汇总 费用报销单_已填写.pdf 费用清单.pdf
```

这将首先合并费用报销单_已填写.pdf和费用清单.pdf，然后合并发票汇总目录中的所有PDF文件，最终输出为费用报销综合.pdf。