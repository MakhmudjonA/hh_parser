# ⚡ HH Parser Pro – HeadHunter Vacancy Intelligence Dashboard

A modern, high-speed, and professional [hh.uz](https://hh.uz) (HeadHunter) vacancy scraper, analytics dashboard, and export tool.
Built with a sleek dark-mode Web UI, complete Docker containerization, interactive analytics with Chart.js, and multi-format export capabilities (Excel, CSV, JSON).

---

## ✨ Features

* 🚀 **High-Speed & Reliable Scraping**: Uses optimized direct stream processing instead of slow, fragile headless browsers. Scrapes 40–100 vacancies in just 1–2 seconds.
* 🐳 **100% Docker-Ready**: Deploy and run anywhere with a single `docker run` command.
* 🎨 **Modern High-Craft Web UI**: Dark theme design, live search, real-time filters, sorting, bento cards, and interactive detail modals.
* 📊 **Live Analytics & Insights**:
  - Average salary calculation (USD & UZS)
  - Remote / Work-from-home share (%)
  - Experience requirement distribution (Doughnut Chart)
  - Top 5 hiring employers (Bar Chart)
* 📥 **Export to 3 Formats**:
  - **CSV (Excel-ready)**: Encoded with UTF-8 BOM so international and Cyrillic characters display cleanly without corruption.
  - **Excel (.xlsx)**: Structured spreadsheet ready for reporting.
  - **JSON**: Clean JSON schema for developer integrations and automation pipelines.
* 🔐 **Account & Session Management**:
  - **Public Safe Mode (Recommended)**: 100% login-free, completely avoiding bot-detection, SMS verification, and interactive captchas.
  - **Session Injection**: Option to supply authenticated session cookies for restricted applicant endpoints.

---

## 🐳 Running with Docker (Recommended)

Ensure Docker Desktop is installed and running:

### Option 1: Single Command (`docker run`)
```bash
# 1. Build the Docker image
docker build -t hh-parser .

# 2. Run the container
docker run -d -p 8000:8000 --name hh_parser_app hh-parser
```

### Option 2: Docker Compose
```bash
docker compose up -d --build
```

Once running, open your browser:
👉 **[http://localhost:8000](http://localhost:8000)**

To stop the container:
```bash
docker stop hh_parser_app
```

---

## 💻 Running Locally (Without Docker)

If you prefer to run the app directly using Python:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   python main.py
   ```
   The application will automatically launch your default browser at **http://localhost:8000**.

---

## 🛠️ API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web Dashboard UI |
| `POST` | `/api/search` | Search and scrape vacancies with filters |
| `GET` | `/api/results` | Retrieve the latest scraped vacancy results |
| `GET` | `/api/stats` | Aggregated metrics, salary averages, and chart data |
| `GET` | `/api/export/csv` | Download results as CSV (UTF-8 BOM) |
| `GET` | `/api/export/excel` | Download results as Excel (.xlsx) |
| `GET` | `/api/export/json` | Download results as JSON |
| `POST` | `/api/auth/login` | Configure optional session cookies |

---

## 📁 Project Structure

```
hh_parser/
├── app.py              # FastAPI server and REST API routes
├── scraper.py          # Optimized HeadHunter scraper engine
├── main.py             # Local runner and browser launcher
├── Dockerfile          # Production Docker container definition
├── docker-compose.yml  # Docker Compose orchestration
├── requirements.txt    # Python dependencies
├── static/
│   └── index.html      # High-Craft Web UI (Tailwind CSS + Lucide + Chart.js)
└── README.md           # Documentation
```
