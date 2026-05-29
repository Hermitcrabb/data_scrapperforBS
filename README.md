# Shopify Better Shipping Data Scraper

## Overview

This project is a **Python-based web scraper** built using **Playwright** to extract shipping configuration data from the **Better Shipping Shopify app**.

It automates:

* Navigation through shipping rate pages
* Extraction of shipping rules, names, postcodes, and pricing
* Handling retries for failed requests
* Exporting structured data into CSV files

---

## Features

* Scrapes all shipping rate IDs across paginated pages
* Extracts:

  * Shipping Name
  * Postcodes
  * Rule Name
  * Rule Type / Product Rules
  * Changed Name
  * Price
* Handles iframe-based UI (Shopify embedded app)
* Retry mechanism for failed IDs
* Separate logging for permanently failed records
* Timestamped CSV export

---

## Tech Stack

* Python 3.x
* Playwright (sync API)
* Pandas

---

## Project Structure

```
.
├── scraper.py          # Main scraping script
├── user_data/          # Persistent browser session (auto-created)
├── Postcodes_*.csv     # Output data file
├── Failedcodes_*.csv   # Failed IDs log
└── README.md
```

---

## Setup Instructions

### 1. Install Dependencies

```bash
pip install playwright pandas
playwright install
```

---

### 2. Run the Script

```bash
python scraper.py
```

---

## Authentication (Important)

This script uses:

```python
launch_persistent_context(user_data_dir="user_data")
```

This means:

* You must **log in manually once**
* Session will be reused automatically

If login expires:

* Delete `user_data/` folder
* Re-run script and login again

Also use ```page.puase()``` to login and create session from google not shopify as it can be used on other stores according to your requirement 
---

## How It Works

### Step 1: Collect Page Numbers

* Scrapes pagination from Shopify UI

### Step 2: Extract Shipping Rate IDs

* Iterates through all pages
* Collects row IDs from the table

### Step 3: Scrape Each ID

For each shipping rate:

1. Opens edit page
2. Extracts:

   * Shipping name
   * Postcodes
3. Navigates to rules page
4. Extracts:

   * Rule name
   * Type / product rules
   * Price

---

## Retry Logic

* Each ID is retried **2 times**
* Failed IDs are retried once more
* Permanently failed IDs are logged separately

---

## Output Files

### Main Data

```
Postcodes_<timestamp>.csv
```

Columns:

* id
* shippingname
* postcodes
* rulename
* rules
* change
* price

---

### Failed Data

```
Failedcodes_<timestamp>.csv
```

Contains:

* IDs that failed after all retries

---

## Notes & Limitations

* Requires stable internet connection
* Shopify UI changes may break selectors
* Uses `wait_for_timeout()` (can be optimized with smarter waits)
* Heavy scraping may trigger Shopify rate limits

---

## Possible Improvements

* Replace static waits with dynamic waits
* Add parallel processing (ThreadPoolExecutor)
* Add logging system (instead of print)
* Export to Excel instead of CSV
* Headless mode support (if Shopify allows)

---

## Author

Pratham Bhandari

---

## License

This project is for internal / educational use.
