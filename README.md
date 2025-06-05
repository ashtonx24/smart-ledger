### everything is subject to be changed soon.
# 💼 Smart Ledger

**A lightweight, offline-first accounting app**  
Tailored for small local businesses who still operate without formal billing systems or POS.  
Built with simplicity, long-term use, and practical utility in mind.

---

## 🧠 Key Features (Planned & Progressive)

- 📅 **Daily Transaction Logging**  
  Record daily income and expenses in a clean, local environment.

- 📈 **Auto & Manual Summaries**  
  Weekly, Monthly, and Custom summaries – viewable on-screen and exportable as PDF.

- 🧾 **Taxation Ready (GST)**  
  Optional GST input, with potential auto-updates via cron/APIs.

- 📊 **Visual Dashboards**  
  End-of-month graphs and business performance charts.

- 🔐 **Offline First, SQLite for Storage**  
  Secure and private. Local only. Easy to use and maintain.

---

## 🔧 Tech Stack

- `Python`
- `Tkinter` for UI
- `SQLite` for local DB (PostgreSQL or MSSQL later, if scaling)
- `ReportLab / FPDF` for PDF
- `Matplotlib / Seaborn` for visualization
- `Cron` / `Windows Task Scheduler` for background tasks (like GST syncs)

---

## 📂 Project Structure

```bash
smart-ledger/
├── database/
│   └── ledger.db
├── ui/
│   └── tkinter_ui.py
├── utils/
│   ├── config.py
│   ├── pdf_generator.py
│   └── summary_tools.py
├── main.py
└── README.md
