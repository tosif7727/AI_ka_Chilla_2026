# 📊 PRD – Steel & Iron Excel-Only POS
**Version 1.0 – 12 Jan 2026**

## 🎯 Vision
Provide a high-performance, offline-first Windows desktop POS for steel traders that manages sales, inventory, and expenses using a transparent, Excel-based storage system.

## 📋 User Stories

| 📌 Story | ✅ Acceptance | 📁 Folder / File |
|----------|--------------|------------------|
| 💰 Record Sale | Inventory auto-deducts KG; receipt prints; row appends to daily file. | `01_SALES/SALE_DD-MM-YYYY.xlsx` |
| 📦 Track Stock | Reorder flag triggered when closing < threshold. | `02_STOCK/STOCK_DD-MM-YYYY.xlsx` |
| 🤝 Manage Suppliers | Paid / Unpaid status tracked; running balance visible. | `03_SUPPLIER/SUPPLIER_DD-MM-YYYY.xlsx` |
| 💳 Log Expenses | Category dropdown; entry appends to daily file. | `04_EXPENSE/EXPENSE_DD-MM-YYYY.xlsx` |
| 📈 Review Business | Reports auto-calculate P&L, cash flow, stock value. | `05_REPORTS/DAILY_DD-MM-YYYY.xlsx` |
| 🔐 Secure Data | Day's five Excel files zipped into EOD backup. | `06_BACKUP/EOD_DD-MM-YYYY.zip` |

## 📊 Excel Schema

| Module | Column Headers | Data Type | 📝 Note |
|--------|----------------|-----------|---------|
| Sales | Timestamp, ItemID, Weight_KG, Rate, Total, PayMode, Status | String, String, Float, Float, Float, String, String | PayMode ∈ {Cash, Credit, UPI, Card} |
| Inventory | ItemID, Opening_KG, In_KG, Out_KG, Closing_KG, Reorder_Flag | String, Float, Float, Float, Float, Boolean | Auto-incremented on sale |
| Supplier | Date, SupplierName, Tonnage, Freight, Total, Paid_Status | Date, String, Float, Float, Float, String | Paid_Status ∈ {Paid, Unpaid} |
| Expense | Date, Category, Amount, Description | Date, String, Float, String | Category dropdown list |
| Reports | Date, TotalSales, TotalPurchase, TotalExpense, Net_PL | Date, Float, Float, Float, Float | Daily / monthly / yearly aggregated |

## ⚙️ Non-Functional Requirements

- **⚡ Performance:** ≤ 1s invoice save on 4-year-old i3 + HDD
- **🔌 Offline:** 100% functional without internet; installer < 100 MB
- **💾 Storage:** Zero database; macro-free `.xlsx` files only
- **🔄 Compatibility:** Excel 2016+ & LibreOffice safe
- **🛠️ Tech Stack:** Python (Tkinter)

## 🚀 Future AI Hooks

- **Reserved Columns:**
    - `AI_Demand_Forecast` (numeric) in STOCK.xlsx
    - `AI_Price_Trend_Prediction` (numeric) in SALE.xlsx
- **Reserved Folder:** `07_AI_MODELS/` for local ML weights or trend logs