from form4 import get_form4_data
from form13f import check_13f
from halal import is_halal
from emailer import send_email


def main():
    print("Starting script...")

    data = get_form4_data()
    print(f"Data received: {data}")

    alerts = []

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

        if not is_halal(item["sector"]):
            print("Skipped: not halal")
            continue

        print("Added to alerts")
        alerts.append(item)

    print(f"Final alerts: {alerts}")

    if not alerts:
        print("No valid alerts today.")
        return

    body = "High Confidence Alerts:\n\n"

    for a in alerts:
        body += f"{a['company']} ({a['ticker']})\n"
        body += f"Insider: {a['insider']}\n"
        body += f"Amount: ${a['amount']:,.2f}\n"
        body += f"Sector: {a['sector']}\n"
        body += "Halal sector check: Passed\n"

        if a.get("institutional_confirmation"):
            body += "13F status: Confirmed\n\n"
        else:
            body += "13F status: Insider-only / not confirmed yet\n\n"

    print("Sending email...")
    send_email("Stock Alert", body)
    print("Email sent!")


if __name__ == "__main__":
    main()