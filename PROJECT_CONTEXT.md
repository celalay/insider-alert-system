# Insider Alert System — Project Context

## Overview

This is a Python-based insider trading alert system.

## Current Capabilities

* Fetches real SEC Form 4 filings using SEC Atom feed
* Extracts filing links and parses ownership XML documents
* Identifies insider transactions
* Filters only open-market purchases (transaction code "P")
* Calculates transaction value (shares × price)
* Removes duplicate transactions
* Applies filters:

  * Minimum amount threshold ($25,000)
  * Optional 13F confirmation
* Sends email alerts via Gmail SMTP
* Uses `.env` for credentials:

  * EMAIL_USER
  * EMAIL_PASS
  * SEC_USER_AGENT

## Project Structure

* src/form4.py → SEC data + parsing
* src/form13f.py → 13F logic (basic/mock)
* src/halal.py → halal filtering (basic)
* src/emailer.py → email sending
* src/main.py → orchestration

## Current Limitation

* Sector is set to "Unknown"
* Halal filtering is not yet meaningful

## Next Goal

* Implement sector lookup using ticker symbols
* Integrate sector into pipeline for halal filtering

## Development Style

* Step-by-step implementation
* Clear explanations
* Progress checks after each step
* Beginner-friendly but production-quality structure
