---
name: "convert_excel_to_pdf"
description: "Converts Excel files to PDF format using win32com. Invoke when user needs to convert .xlsx/.xls files to PDF documents."
---

# Excel to PDF Converter

This skill converts Excel files to PDF format using Microsoft Excel COM automation.

## Functionality

- Converts Excel files (.xlsx, .xls) to PDF format
- Uses `win32com.client` to interact with Excel application
- Runs Excel in background mode (invisible)
- Handles conversion errors gracefully

## Usage

Invoke this skill when:
- User needs to convert an Excel file to PDF
- User has a spreadsheet that needs to be shared as PDF
- Batch conversion of multiple Excel files is required

## Parameters

The conversion requires:
1. **Excel file path**: Source file (.xlsx or .xls)
2. **PDF file path**: Destination file path for output

## Implementation Details

The conversion process:
1. Dispatches Excel.Application COM object
2. Opens the Excel workbook
3. Exports to PDF using `ExportAsFixedFormat(0, pdf_path)`
4. Closes workbook without saving changes
5. Quits Excel application
6. Returns success/failure status

## Error Handling

- Catches and logs conversion errors
- Ensures Excel application is always quit (finally block)
- Returns boolean success status

## Requirements

- Windows operating system
- Microsoft Excel installed
- Python `pywin32` package installed
