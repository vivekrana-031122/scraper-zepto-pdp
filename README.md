# Zepto PDP Quick Commerce Scraper

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tech: Scrapy](https://img.shields.io/badge/Tech-Scrapy-brightgreen.svg)](#)

> [!NOTE]
> This scraper is fully functional but not scheduled to run automatically. Run manually with `python zepto_pdp_spider.py`.


Scrapy-based spider designed to extract Product Detail Page (PDP) information (prices, ratings, stock availability) from Zepto based on specific locations and pincodes.

---

## 🚀 Features

* Leverages Scrapy's fast asynchronous networking
* Queries dynamic web endpoints to extract real-time product prices and ratings
* Implements custom cookies and headers to simulate active consumer sessions
* Persists data into structured database tables
* Connects to MySQL or falls back to a zero-config local SQLite database

---

## 🛠️ Tech Stack & Libraries
* **Language:** Python 3.8+
* **Libraries:** Scrapy, PyMySQL, Python

---

## 📦 Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/vivekrana-031122/scraper-zepto-pdp.git
   cd scraper-zepto-pdp
   ```

2. **Create and Activate a Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Additional Setup (if applicable):**
   * If using Playwright:
     ```bash
     playwright install chromium
     ```

---

## 💻 Usage Example

Run the main scraper entry point:
```bash
scrapy crawl zepto_pdp -a pf_id=1 -a sku_id=101 -a web_pid=prod123 -a page_url=https://shop.zeptonow.com/Home -a location=Mumbai -a location_id=1 -a pincode=400001 -a crawl_id=1 -a brand_id=5 -a brand_name=Amul -a env=prod -a db_name=zepto
```

---

## 🛡️ Disclaimer & Robots.txt Compliance

This project is created for educational and professional demonstration purposes. By using this tool, you agree to:
* Respect the target website's `robots.txt` directives.
* Avoid making aggressive requests that could disrupt target servers (configure appropriate sleep intervals/throttling).
* Comply with local web data protection regulations and the platform's terms of service.
