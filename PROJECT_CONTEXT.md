# Insider Alert System — Project Context

## Overview

Python-based insider trading alert system that monitors SEC Form 4 filings and sends filtered alerts via email.

---

## Current Capabilities

### Data Pipeline

* Fetches real SEC Form 4 filings using SEC Atom feed
* Extracts filing links and resolves ownership XML
* Parses insider transaction data from XML

### Filtering Logic

* Detects open-market purchases (transaction code "P")
* Calculates transaction value (shares × price)
* Removes duplicate transactions

### Filters Applied

* Minimum transaction amount threshold (default: $25,000)
* Sector lookup using ticker (via yfinance)
* Halal filtering based on sector
* Size-aware 13F institutional signal using market cap plus `yfinance` holder data
* Fund-level snapshot in alerts: holder name, shares, % of company, value, and proxy trend note
* Two-level 13F wording in email output: `needs_to_be_validate` / `most_probably_no`

### Alert System

* Sends email alerts via Gmail SMTP
* Uses `.env` for credentials:

  * EMAIL_USER
  * EMAIL_PASS
  * SEC_USER_AGENT

### Email Output Includes

* Company name + ticker
* Insider name
* Transaction amount (formatted)
* Sector
* Halal status:

  * `needs_to_be_validate`
  * `most_probably_no`
* 13F status and note
* Institutional-holder context based on company size

Defaults

- Form 4 fetch window: last 24 hours by default (no widening)

---

## Project Structure

* `src/form4.py` → SEC feed + XML parsing + purchase detection
* `src/form13f.py` → size-aware 13F institutional signal logic
* `src/halal.py` → sector-based halal filtering
* `src/sector_lookup.py` → ticker → sector via yfinance
* `src/emailer.py` → email sending logic
* `src/main.py` → main pipeline orchestration

---

## Current System Behavior

* Real-time SEC insider purchase detection is working
* Sector lookup is integrated and functioning
* Halal filtering is active and verifiable in email output
* Duplicate transactions are handled
* Alerts include institutional context even when a company does not meet the 13F confirmation threshold

---

## Known Limitations

* 13F logic currently uses `yfinance` market cap and institutional holder data as a proxy, not full SEC quarter-by-quarter filing comparison
* Quarter-over-quarter change is still a placeholder in the current proxy output
* Sector-based halal filtering is simplified (not finance-grade)
* No scheduling (manual execution only)
* No database/history tracking

---

## Next Goals (Priority Order)

1. Replace the 13F proxy with real SEC quarter-over-quarter filing comparison
2. Add fund-level trend detection: new positions, increases, decreases, and exits
3. Add scheduling (daily automation)
4. Improve halal filtering accuracy (API or dataset-based)
5. Improve email formatting (summary + ranking)
6. Add logging / persistence

---

## Development Style

* Step-by-step implementation
* Clear explanations
* Progress validation after each step
* Beginner-friendly, production-minded approach

## How to Run

### Setup

1. Create virtual environment
2. Install dependencies:
  pip install -r requirements.txt

### Environment Variables (.env)

EMAIL_USER=[your_email@gmail.com](mailto:your_email@gmail.com)
EMAIL_PASS=your_app_password
SEC_USER_AGENT=[your_email@gmail.com](mailto:your_email@gmail.com)

### Run the System

python src/main.py

---

## Notes

* `.env` is not tracked in Git (security)
* System is currently run manually (no scheduler yet)
* Uses live SEC data (results vary per run)
