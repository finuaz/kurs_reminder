# 💱 Kurs Reminder (USD/IDR)

A lightweight **USD → IDR exchange rate monitor** that scrapes **BCA e-Rate**, compares it with **market reference rates**, sends **notifications when thresholds are crossed**, and records **structured data** for long-term analysis and future AI insights.

---

## ✨ Features

- 🏦 Scrape **BCA USD/IDR e-Rate** (buy & sell)
- 📊 Compare with **market reference rate** (FT Markets, delayed)
- 🔔 Send notifications via **ntfy.sh**
- 🧾 Record every run into **monthly JSONL logs**
- 🕒 Timestamp-aware (observed time vs reference time)
- 🧠 Designed for future **AI / analytical workflows**
- ⚙️ Runs locally, on **GitHub Actions**, or on a **server (cron-ready)**

---

## 🗂 Project Structure

```
kurs_reminder/
├── main.py              # Main runner (scrape → notify → record)
├── recorder.py          # JSONL recorder module
├── requirements.txt     # Python dependencies
├── data/
│   └── rates/
│       └── usd_idr_YYYY-MM.jsonl
└── .github/
    └── workflows/       # GitHub Actions workflows (optional)
```

---

## 🔔 Notification Logic

- Thresholds are defined in code (example: `15000 → 17500`, step `100`)
- When the current **USD buy rate ≥ threshold**:
  - A notification is sent via **ntfy.sh**
- Each threshold triggers **once per run**

---

## 🧾 Recorded Data Format (JSONL)

Each execution appends **one record** to a monthly file:

```json
{
  "run_id": "uuid",
  "timestamp": "2025-12-23T10:15:00+07:00",
  "rate_buy": 16700,
  "rate_sell": 16800,
  "reference_rate": 16744,
  "reference_source": "ft_markets",
  "reference_timestamp": "2025-12-22T22:49:00Z",
  "reference_delay_minutes": 15,
  "thresholds_triggered": [16500],
  "notification_count": 1,
  "latency_ms": 612,
  "environment": "local",
  "schema_version": 1
}
```

Reasons for using JSONL:

- Append-only
- Crash-safe
- Easy to merge, stream, and process later

---

## 🚀 How to Run (Local)

### 1️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 2️⃣ Run once

```bash
python main.py
```

### 3️⃣ Run periodically (optional)

You can:

- Uncomment the loop inside `main.py`
- Use `cron` (Linux / VPS)
- Use Windows Task Scheduler
- Use GitHub Actions (scheduled workflow)

---

## 🤖 GitHub Actions (Optional)

This project can run on **GitHub Actions (public repo, free)**.

The GitHub Actions runner filesystem is **temporary**.  
Recorded logs are available only if uploaded as **artifacts**.

Example artifact upload step:

```yaml
- name: Upload rate logs
  uses: actions/upload-artifact@v4
  with:
    name: rate-logs
    path: data/rates/
    retention-days: 30
```

Artifacts can be downloaded from:  
**Actions → Workflow run → Artifacts**

---

## ☁️ Long-Term Storage (Optional)

For permanent storage beyond GitHub artifact retention, you can:

- Upload logs to **Amazon S3**
- Store logs on a **VPS with persistent disk**
- Migrate to a database later (SQLite or time-series DB)

The codebase is structured so storage strategy can evolve without changing core logic.

---

## 🧠 Design Notes

- This project focuses on **observation**, not trading
- Bank rates, market rates, and reference rates represent **different perspectives**
- The recorder module is intentionally **write-only and decoupled**

---

## 📜 License

MIT License
