import os
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from pathlib import Path
from sector_lookup import get_sector

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SEC_USER_AGENT = os.getenv("SEC_USER_AGENT")


def get_form4_data():
    url = "https://www.sec.gov/cgi-bin/browse-edgar"

    params = {
        "action": "getcurrent",
        "type": "4",
        "count": "100",
        "output": "atom"
    }

    headers = {
        "User-Agent": SEC_USER_AGENT
    }

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()

    print("SEC Form 4 feed fetched successfully.")

    root = ET.fromstring(response.text)

    namespace = {
        "atom": "http://www.w3.org/2005/Atom"
    }

    filings = []

    for entry in root.findall("atom:entry", namespace):
        title = entry.find("atom:title", namespace).text

        link_element = entry.find("atom:link", namespace)
        filing_url = link_element.attrib.get("href") if link_element is not None else None

        updated = entry.find("atom:updated", namespace).text

        filing = {
            "title": title,
            "filing_url": filing_url,
            "updated": updated
        }

        filings.append(filing)

    print(f"Parsed {len(filings)} Form 4 filings.")

    all_results = []
    seen = set()

    for filing in filings:
        xml_url = extract_xml_link(filing["filing_url"])

        if not xml_url:
            continue

        try:
            results = parse_ownership_xml(xml_url)
            for result in results:
                unique_key = (
                    result["company"],
                    result["ticker"],
                    result["insider"],
                    result["amount"]
                )

                if unique_key in seen:
                    continue
                seen.add(unique_key)
                all_results.append(result)
        except Exception as e:       
            print("Error processing filing:", e)

    print(f"\nFound {len(all_results)} purchase transactions.")

    for r in all_results:
        print(r)

    return all_results

def extract_xml_link(filing_url):
    headers = {
        "User-Agent": SEC_USER_AGENT
    }

    response = requests.get(filing_url, headers=headers)
    response.raise_for_status()

    html = response.text

    # Simple way: find first XML file link
    start = html.find(".xml")
    if start == -1:
        return None

    # backtrack to find href
    href_start = html.rfind("href=", 0, start)
    if href_start == -1:
        return None

    quote_start = html.find('"', href_start) + 1
    quote_end = html.find('"', quote_start)

    xml_path = html[quote_start:quote_end]

    if xml_path.startswith("/"):
        xml_url = "https://www.sec.gov" + xml_path
    else:
        xml_url = xml_path

    if "/xslF345X" in xml_url:
        parts = xml_url.split("/")
        xml_url = "/".join(parts[:-2] + [parts[-1]])

    return xml_url

def preview_xml(xml_url):
    headers = {
        "User-Agent": SEC_USER_AGENT
    }

    response = requests.get(xml_url, headers=headers)
    response.raise_for_status()

    print("\n--- XML Preview ---")
    print(response.text[:1500])

def parse_ownership_xml(xml_url):
    headers = {
        "User-Agent": SEC_USER_AGENT
    }

    response = requests.get(xml_url, headers=headers)
    response.raise_for_status()

    root = ET.fromstring(response.text)

    def get_text(path):
        element = root.find(path)
        return element.text if element is not None else None

    issuer_name = get_text("issuer/issuerName")
    ticker = get_text("issuer/issuerTradingSymbol")
    insider_name = get_text("reportingOwner/reportingOwnerId/rptOwnerName")

    results = []

    for transaction in root.findall("nonDerivativeTable/nonDerivativeTransaction"):
        code = transaction.findtext("transactionCoding/transactionCode")

        # ONLY keep real purchases
        if code != "P":
            continue

        shares = transaction.findtext("transactionAmounts/transactionShares/value")
        price = transaction.findtext("transactionAmounts/transactionPricePerShare/value")

        try:
            shares = float(shares)
            price = float(price)
            amount = shares * price
        except:
            continue

        sector = get_sector(ticker)

        result = {
            "company": issuer_name,
            "ticker": ticker,
            "insider": insider_name,
            "amount": amount,
            "sector": sector
        }

        results.append(result)

    return results