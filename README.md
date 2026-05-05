# Insider Alert System

Python-based insider trading alert system that monitors SEC Form 4 filings, filters purchase alerts, and sends email notifications.

## What It Does

- Pulls live SEC Form 4 filings from the SEC Atom feed
 - Pulls live SEC Form 4 filings from the SEC Atom feed
- Parses ownership XML and keeps open-market purchase transactions
- Aggregates multiple purchases from the same insider into one total amount
- Looks up the company sector through `yfinance`
- Filters out non-halal sectors with a simple sector-name check
- Applies a size-aware 13F institutional signal using market cap and `yfinance` holder data
- Shows fund-level 13F details in the email: holder name, shares, percent of company, value, and a proxy trend note
- Uses a two-level email structure: `Needs to be Validate` and `Most Probably NO`
- Sends the final alerts by Gmail SMTP

Defaults:

- Form 4 fetch window: last 24 hours by default (no widening)

## Project Layout

- `src/form4.py` - SEC feed fetching, XML parsing, purchase detection, aggregation
- `src/form13f.py` - Size-aware 13F institutional signal logic
- `src/halal.py` - Sector-based halal filtering
- `src/sector_lookup.py` - Ticker-to-sector lookup using `yfinance`
- `src/emailer.py` - Gmail SMTP email sending
- `src/main.py` - Main pipeline orchestration
- `tests/test_pipeline.py` - Unit tests for the core pipeline and support modules

## Setup

1. Create and activate your virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root with:

```env
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
SEC_USER_AGENT=your_email@gmail.com
```

## Run The App

```bash
python src/main.py
```

This is the live end-to-end run. It fetches real SEC data and sends an email if alerts are found.

## Run The Tests

Use the test suite to verify the important pieces without hitting live services:

```bash
python -m unittest discover -s tests
```

## What The Tests Cover

- Form 4 aggregation behavior
- The main pipeline using realistic alert-shaped sample data
- Halal filtering rules
- Sector lookup behavior with mocked `yfinance`
- Size-aware 13F institutional signal behavior
- Fund-level 13F detail formatting in the email body
- Email message construction and SMTP usage with mocked Gmail

## Expected Output

When the app is healthy, a manual run will usually print messages like:

- `SEC Form 4 feed fetched successfully.`
- `Parsed ... Form 4 filings.`
- `Found ... aggregated purchase alerts.`
- `Sending email...`
- `Email sent!`

When the tests are healthy, you should see something like:

```text
Ran 11 tests in ...

OK
```

## Troubleshooting

- If `python src/main.py` fails with an import error, run it from the project root.
- If SEC requests fail, confirm `SEC_USER_AGENT` is set in `.env` to a valid email-style user agent.
- If email sending fails, verify `EMAIL_USER` and `EMAIL_PASS` are correct Gmail credentials.
- If a recent change breaks behavior, rerun `python -m unittest discover -s tests` to isolate the failing component.

## Debugging A Failed Run

If the manual run fails, check the app in this order:

1. Verify the virtual environment is active.
2. Confirm the `.env` file exists in the project root and has the three required variables.
3. Run the test suite first to confirm the local code path is healthy.
4. Run `python src/main.py` again and compare the printed output with the expected output above.

The `.env` file is meant to stay local and should not be committed.

## Notes

- The app currently runs manually.
- 13F logic is currently a market-cap-aware institutional proxy, not full SEC quarter-over-quarter filing comparison.
- Quarter-over-quarter change is not yet calculated from SEC 13F filing history.
- The system uses live SEC data, so results vary by run.