from form4 import get_form4_data
from form13f import check_13f
from halal import evaluate_halal
from emailer import send_email


def main():
    print("Starting script...")

    data = get_form4_data(days_back=1)
    if not data:
        print("No qualifying alerts in the last 24 hours. No alerts to report.")
        return

    print(f"Data received: {data}")

    safe_alerts = []
    blocked_alerts = []

    for item in data:
        print(f"Checking item: {item}")

        if item["amount"] < 2000:
            print("Skipped: amount too low")
            continue

        institutional_signal = check_13f(item["ticker"])
        item["institutional_signal"] = institutional_signal
        item["institutional_confirmation"] = institutional_signal["is_confirmed"]

        print(
            "13F check: "
            f"{institutional_signal['status']} - {institutional_signal['reason']}"
        )

        halal_decision = evaluate_halal(item["sector"])
        item["halal_status"] = halal_decision["status"]
        item["halal_reason"] = halal_decision["reason"]

        if halal_decision["is_halal"]:
            print(f"Added to safe alerts: {halal_decision['reason']}")
            safe_alerts.append(item)
        else:
            print(f"Added to blocked alerts: {halal_decision['reason']}")
            blocked_alerts.append(item)

    print(f"Final safe alerts: {safe_alerts}")
    print(f"Final blocked alerts: {blocked_alerts}")

    if not safe_alerts and not blocked_alerts:
        print("No valid alerts today.")
        return

    body = "Needs to be Validate:\n\n"

    if safe_alerts:
        for a in safe_alerts:
            body += f"{a['company']} ({a['ticker']})\n"
            body += f"Insiders: {a['insider']}\n"
            body += f"Total insider purchase amount: ${a['amount']:,.2f}\n"
            body += f"Sector: {a['sector']}\n"
            body += f"Halal sector check: {a.get('halal_status', 'needs_to_be_validate')}\n"
            body += f"13F status: {a['institutional_signal']['status']}\n"
            body += f"13F summary: {a['institutional_signal'].get('summary', 'unavailable')}\n"
            body += f"13F note: {a['institutional_signal']['reason']}\n\n"
            body += _format_top_funds(a['institutional_signal'])

    body += "Most Probably NO:\n\n"

    if blocked_alerts:
        for a in blocked_alerts:
            body += f"{a['company']} ({a['ticker']})\n"
            body += f"Insiders: {a['insider']}\n"
            body += f"Total insider purchase amount: ${a['amount']:,.2f}\n"
            body += f"Sector: {a['sector']}\n"
            body += f"Halal sector check: {a.get('halal_status', 'most_probably_no')}\n\n"
            body += f"13F status: {a['institutional_signal']['status']}\n"
            body += f"13F summary: {a['institutional_signal'].get('summary', 'unavailable')}\n"
            body += f"13F note: {a['institutional_signal']['reason']}\n\n"
            body += _format_top_funds(a['institutional_signal'])

    print("Sending email...")
    send_email("Stock Alert", body)
    print("Email sent!")


def _format_top_funds(institutional_signal):
    top_funds = institutional_signal.get("top_funds", [])

    if not top_funds:
        return "Top funds: none found in current institutional snapshot\n\n"

    body = "Top funds:\n"
    major_fund_count = institutional_signal.get("major_fund_count", 0)

    body += f"Major funds detected: {major_fund_count}\n"

    for fund in top_funds:
        summary_line = fund.get("summary_line") or fund.get("holder", "Unknown fund")
        percent_of_company = fund.get("percent_of_company")
        shares = fund.get("shares")
        value = fund.get("value")

        body += f"- {summary_line}\n"

        detail_bits = []
        if percent_of_company is not None:
            detail_bits.append(f"percent: {percent_of_company}")
        if shares is not None:
            detail_bits.append(f"shares: {shares}")
        if value is not None:
            detail_bits.append(f"value: ${value:,.2f}")

        body += f"  {'; '.join(detail_bits)}\n"

    return body + "\n"


if __name__ == "__main__":
    main()
