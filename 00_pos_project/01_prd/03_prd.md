# Product Requirement Document (PRD)
## Project: Fazal N Son's POS (Iron & Steel Edition)

| Document Control | Details |
| :--- | :--- |
| **Project Name** | Iron & Steel POS System |
| **Client** | **Fazal N Son's** |
| **Development Lead** | **Codanics** |
| **Version** | 3.0 (Final Release Candidate) |
| **Status** | Approved for Development |
| **Date** | 19 Jan 2026 |

---

## 1. Executive Summary
**Fazal N Son's POS** is a mission-critical, standalone desktop application designed to digitize the operations of a high-volume Iron & Steel warehouse in Pakistan. It replaces manual registers ("Bahi Khata") with a secure, offline-first, visual software solution.

The system is engineered to handle the specific complexities of the steel trade—**Weight-based sales (Tons/Mann)**, **Credit Management (Udhaar)**, and **Gate Pass generation**—while remaining accessible to semi-literate warehouse staff through a visual, Urdu-first interface.

### 1.1 Business Objectives
1.  **Eliminate Calculation Errors:** Automate complex weight conversions (e.g., Feet to Kg for Garder/Beams).
2.  **Digitize Credit (Udhaar):** Track customer outstanding balances and installment history accurately.
3.  **Theft Prevention:** Real-time stock alerts and strict "Cash in Hand" reconciliation.
4.  **Operational Velocity:** Reduce billing time from ~5 minutes (manual) to <30 seconds.

---

## 2. Product Scope

### 2.1 In-Scope features
-   **Point of Sale (POS):** Visual grid, fast billing, weight calculation.
-   **Customer Ledger (Khata):** Credit sales, recoveries, installments.
-   **Inventory (Godown):** Stock tracking, low stock alerts, simple audit.
-   **Supplier Management:** Inward stock recording, mill payments.
-   **Expense Management:** Daily warehouse expenses (Tea, Labor, Freight).
-   **Reporting:** Excel-only exports for owner review.

### 2.2 Out-of-Scope
-   Cloud Synchronization (Strictly Offline).
-   Multi-branch real-time networking (Future Phase).
-   E-commerce integration.

---

## 3. User Personas

| Persona | Role | Key Characteristics | Goals |
| :--- | :--- | :--- | :--- |
| **Munshi Ji / Chotu** | Operator | Semi-literate. Knows steel types visually. Intimidated by English text/complex forms. | Generate bills quickly. Avoid calculation mistakes. |
| **Seth Sahab** | Owner | Business Owner. Reviewer. Trusts Excel and Physical Cash. | Prevent theft. Monitor "Cash in Hand". Track "Who owes me money". |

---

## 4. Functional Specifications

### 4.1 Module: Point of Sale (The Weighbridge)
*The core interface for creating Sales Invoices.*

**POS-01: Visual Product Catalog**
-   **Requirement:** Display products as a 4x5 grid of large images/icons.
-   **Categories:** Sarya (Rebar), Garder (Beam), Channel, Angle, Sheet (Chadar).
-   **UI Action:** Single tap adds item to cart. Long press opens "Quick Edit".

**POS-02: Advanced Weight Logic**
-   **Requirement:** Support multi-unit entry.
-   **Logic:**
    -   *Sarya:* Input Weight (Kg) OR Bundles.
    -   *Garder/Beam:* Input Length (Feet) -> Auto-calculate Weight (Kg) based on density factor.
    -   *Sheet:* Input Size (4x8) + Gauge -> Auto-calculate Weight.

**POS-03: Hold & Estimate (Kacha Bill)**
-   **Requirement:** Ability to print a "Quotation" without affecting inventory/accounting.
-   **Use Case:** Contractor asks for rates for 5 Tons of steel. Munshi prints estimate.

---

### 4.2 Module: Customer Credit & Ledger (Udhaar)
*Comprehensive management of A/R with per-customer history.*

**CRED-01: Credit Sale Workflow**
-   **Trigger:** Checkout -> Payment Mode "Credit / Udhaar".
-   **Action:** Assign to Customer (e.g., "Contractor Saleem").
-   **Logic:** `Customer Balance = Previous Balance + Current Bill Amount`. Stock deducted immediately.

**CRED-02: Payment Recovery (Wasooli) & Installments**
-   **Requirement:** Handle partial or full payments securely.
-   **Workflow:**
    1.  Open `Customer Ledger` -> Select Name.
    2.  Show **Total Loan (Udhaar)**: e.g., *Rs. 500,000*.
    3.  Click **"Receive Payment"** button.
    4.  Enter Amount: e.g., *Rs. 50,000* (Installment).
    5.  **Deduction Logic:** `New Balance = 500,000 - 50,000 = 450,000`.
-   **Output:** Print "Recovery Receipt" showing Old Balance, Paid Amount, and New Remaining Balance.

**CRED-03: Individual Sales History**
-   **Requirement:** Click any customer name to see their full timeline.
-   **View:** List of all bills taken on date and all payments made on date.
-   **Transparency:** Clicking a Bill ID shows what items explain that loan.

---

### 4.3 Module: Sales Return & Damage (Wapsi)
*Handling items sent back by customers due to damage or excess.*

**RET-01: Return Process (Wapsi)**
-   **Scenario:** Driver brings back 10 Garder (beams) because they were extra.
-   **Action:** `Sales History` -> `Find Bill #123` -> Click **"Return Items"**.
-   **Selection:** Select the 10 Garder items -> Confirm Return.

**RET-02: Refund Type Logic**
The system acts based on the original payment method:
1.  **Cash Refund:** If bill was Cash, system asks "Give Cash Back?". Use `Cash In Hand`.
2.  **Credit Adjustment:** If bill was Udhaar, system **Automaticall Reduces** the customer's loan.
    -   *Logic:* `Customer Balance = Customer Balance - Returned Amount`.

**RET-03: Stock Effect (Damage vs Restock)**
-   **Question:** System asks: "Is item Good or Damaged?"
    -   **Good:** Add quantity back to `Inventory Level`.
    -   **Damaged:** Move to `Scrap / Wastage` bin (Do not sell again).

---

### 4.4 Module: Expenses & Cash Flow
**EXP-01: Daily Warehouse Expenses**
-   **Requirement:** Quick-log buttons for:
    -   *Langar/Roti* (Food).
    -   *Bhara* (Freight/Loading).
    -   *Salary/Advance* (Staff payments).

**EXP-02: Cash Reconciliation**
-   **Formula:** `Opening Cash + Cash Sales + Recoveries - Expenses - Supplier Payments = Closing Cash`.
-   **Alert:** If physical cash < system cash, flag as "Shortage".

---

## 5. Non-Functional Requirements (NFR)

1.  **Reliability (Offline Integrity):** System must function 100% without internet. Database (`.db` file) must be resilient to power failures (WAL mode enabled in SQLite).
2.  **Performance:**
    -   App Launch: < 3 seconds.
    -   Product Search: < 100ms.
    -   Hardware Target: Core 2 Duo / Core i3, 4GB RAM, HDD.
3.  **Data Security:**
    -   Local Backups: Auto-create `.zip` backup of database to D:/Audit/ daily on close.
    -   No external cloud dependencies preventing vendor lock-in.

---

## 6. UI/UX Design Guidelines

-   **Language:** Hybrid Urdu/English.
    -   Primary Labels: Urdu (Nastaliq or Naskh).
    -   Secondary: English (Arial/Inter).
-   **Color Palette (Industrial):**
    -   **Primary:** Steel Blue (#4A6FA5).
    -   **Action:** Safety Orange (#FF6B35) for "Checkout/Print".
    -   **Credit/Danger:** Rust Red (#C0392B) for "Udhaar" or "Low Stock".
    -   **Safe:** Industrial Green (#27AE60) for "Cash Received".
-   **Accessibility:** Font size minimum 16px. High contrast for low-light godown environments.

---

## 7. Technical Architecture

| Component | Choice | Reason |
| :--- | :--- | :--- |
| **Framework** | **Electron** | Cross-platform desktop capabilities (Printing, File System access). |
| **Frontend** | **React.js** | Component-based UI for complex visual grids and state management. |
| **Styling** | **Tailwind CSS** | Rapid styling, easy scaling for responsiveness. |
| **Database** | **SQLite 3** | Zero-configuration, serverless, single-file database. Ideal for standalone apps. |
| **Export Engine** | **SheetJS** | Reliable Excel generation for owner reporting. |

---

## 8. Glossary
-   **Sarya:** Rebar / Steel Reinforcement bars.
-   **Garder:** I-Beams / T-Irons.
-   **Soot:** Measurement unit (1/8th of an inch).
-   **Roznamcha:** Daily Journal / Day Book.
-   **Khata:** Ledger / Account.
-   **Munshi:** Clerk / Accountant.

---
*End of Document*
