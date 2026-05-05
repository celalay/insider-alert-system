from form4 import get_form4_data
from form13f import check_13f
from halal import evaluate_halal
from emailer import send_email


def main():
    print("Starting script...")

    data = get_form4_data()
    print(f"Data received: {data}")

    safe_alerts = []
    blocked_alerts = []

    for item in data:
        print(f"Checking item: {item}")

        if item["amount"] < 2000:
            print("Skipped: amount too low")
            continue

        item["institutional_confirmation"] = check_13f(item["ticker"])

        if item["institutional_confirmation"]:
            print("13F confirmation found")
        else:
            print("No 13F confirmation — keeping as insider-only alert")

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

            if a.get("institutional_confirmation"):
                body += "13F status: Confirmed\n\n"
            else:
                body += "13F status: Insider-only / not confirmed yet\n\n"

    body += "Most Probably NO:\n\n"

    if blocked_alerts:
        for a in blocked_alerts:
            body += f"{a['company']} ({a['ticker']})\n"
            body += f"Insiders: {a['insider']}\n"
            body += f"Total insider purchase amount: ${a['amount']:,.2f}\n"
            body += f"Sector: {a['sector']}\n"
            body += f"Halal sector check: {a.get('halal_status', 'most_probably_no')}\n\n"

    print("Sending email...")
    send_email("Stock Alert", body)
    print("Email sent!")


if __name__ == "__main__":
    main()
