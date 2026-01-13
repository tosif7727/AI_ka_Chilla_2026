# 📊 PRD – Steel & Iron Excel-Only POS
**Version 1.1 – 12 Jan 2026**
*(added file-level credential protection)*

## 🎯 Vision
Provide a high-performance, offline-first Windows desktop POS for steel traders that manages sales, inventory, and expenses using a password-protected, view-only Excel-based storage system.

## 📖 User Stories (new rows in bold)
| Story                                                                                                             | Acceptance                                                                                                                                                     | Folder / File Impacted                                                   |
| ----------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **💰 Record Sale** …                                                                                                 | …                                                                                                                                                              | `01_SALES/SALE_DD-MM-YYYY.xlsx`                                          |
| **📦 Track Stock** …                                                                                                 | …                                                                                                                                                              | `02_STOCK/STOCK_DD-MM-YYYY.xlsx`                                         |
| **🤝 Manage Suppliers** …                                                                                            | …                                                                                                                                                              | `03_SUPPLIER/SUPPLIER_DD-MM-YYYY.xlsx`                                   |
| **💸 Log Expenses** …                                                                                                | …                                                                                                                                                              | `04_EXPENSE/EXPENSE_DD-MM-YYYY.xlsx`                                     |
| **📈 Review Business** …                                                                                             | …                                                                                                                                                              | `05_REPORTS/*.xlsx`                                                      |
| **🔒 Secure Data** …                                                                                                | …                                                                                                                                                              | `06_BACKUP/EOD_DD-MM-YYYY.zip`                                           |
| **🛡️ Protect Files**<br>As an owner I want critical files to open **read-only** unless a master password is entered. | System prompts for master password when user clicks "Edit Mode"; without it files open in view-only mode. Excel workbook-level write password set at creation. | `01_SALES…xlsx`, `02_STOCK…xlsx`, `03_SUPPLIER…xlsx` (owner selectable). |

## 📋 Excel Schema (unchanged columns, added protection column)
| Module | Column Headers | Data Type | Protection Level |
|--------|---|---|---|
| Sales | … | … | Write-password (owner) |
| Inventory | … | … | Write-password (owner) |
| Supplier | … | … | Write-password (owner) |
| Expense | … | … | Optional password |
| Reports | … | … | View-only (no password) |

### Implementation:
- 🔐 POS generates file with Workbook.WriteResPassword = <master>
- 👁️ Viewer role opens file read-only; prompt only when "Edit" button clicked
- 📦 Backup zip not password-protected (owner can add externally if needed)

## ⚙️ Non-Functional Requirements

- **⚡ Performance:** ≤ 1s invoice save on 4-year-old i3 + HDD
- **🔌 Offline:** 100% functional without internet; installer < 100 MB
- **💾 Storage:** Zero database; macro-free `.xlsx` files with optional workbook-level write passwords
- **🔄 Compatibility:** Excel 2016+ & LibreOffice safe
- **🛠️ Tech Stack:** Python (Tkinter)
- **🔐Security:** Master password hashed (SHA-256) in local settings.ini; never stored in plain text

## 🤖 Future AI Hooks (unchanged)
- **Reserved Columns:** AI_Demand_Forecast, AI_Price_Trend_Prediction
- **Reserved Folder:** 07_AI_MODELS/