---
name: "update-reimbursement-info"
description: "更新报销单中的页数和报销人信息。当需要更新费用报销单的页数和报销人信息时调用。"
---

# Update Reimbursement Info

此技能用于更新费用报销单中的页数和报销人信息。

## 功能

- 更新Excel报销单中的J3单元格，设置为"单据及附件共X页"格式
- 更新Excel报销单中的I9单元格，设置报销人姓名
- 保存修改后的Excel文件

## 使用场景

当费用报销单需要更新页数和报销人信息时使用此技能。

## 参数

- `file_path`: Excel报销单文件路径
- `page_count`: 报销单总页数
- `reimbursename`: 报销人姓名

## 示例

```python
python update_reimbursement_info.py 费用报销单_已填写.xlsx 11 程文清
```