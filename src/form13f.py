import yfinance as yf
from datetime import datetime


LARGE_CAP_THRESHOLD = 10_000_000_000
MID_CAP_THRESHOLD = 1_000_000_000
MAJOR_FUND_VALUE_THRESHOLD = 100_000_000


def _get_company_size(market_cap):
    if market_cap is None:
        return "unknown"

    if market_cap >= LARGE_CAP_THRESHOLD:
        return "large"

    if market_cap >= MID_CAP_THRESHOLD:
        return "mid"

    return "small"


def _required_holders_for_size(company_size):
    if company_size == "large":
        return 3

    if company_size == "mid":
        return 2

    return 1


def _format_reason(company_size, holder_count, required_holders):
    if holder_count >= required_holders:
        return f"{holder_count} institutional holders found for a {company_size}-cap company"

    if holder_count > 0:
        return f"Limited institutional coverage for a {company_size}-cap company ({holder_count}/{required_holders})"

    if company_size == "small":
        return "Small company with limited institutional coverage"

    return f"No institutional holders found for a {company_size}-cap company"


def _format_percent(value):
    if value is None:
        return None

    try:
        if isinstance(value, str):
            cleaned_value = value.strip().replace("%", "")
            return f"{float(cleaned_value):.2f}%"

        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return None


def _format_date(date_reported):
    if date_reported is None:
        return None

    if isinstance(date_reported, datetime):
        return date_reported.strftime("%Y-%m-%d")

    try:
        return str(date_reported)[:10]
    except Exception:
        return None


def _build_summary_line(holder_name, ticker, percent_of_company, date_reported):
    if percent_of_company:
        summary = f"{holder_name} — Hold {ticker} ({percent_of_company})"
    else:
        summary = f"{holder_name} — Hold {ticker}"

    formatted_date = _format_date(date_reported)
    if formatted_date:
        summary += f" as of {formatted_date}"

    return summary


def _format_snapshot_summary(company_size, holder_count, required_holders, top_funds):
    major_funds = [fund for fund in top_funds if (fund.get("value") or 0) >= MAJOR_FUND_VALUE_THRESHOLD]
    major_fund_count = len(major_funds)

    if holder_count == 0:
        return {
            "snapshot_label": "no_institutional_snapshot",
            "summary": "No institutional holders are visible in the current snapshot.",
            "major_fund_count": 0,
        }

    if holder_count < required_holders:
        return {
            "snapshot_label": "light_support",
            "summary": (
                f"Current snapshot shows {holder_count} institutional holder(s), "
                f"which is still limited for a {company_size}-cap company."
            ),
            "major_fund_count": major_fund_count,
        }

    if major_fund_count > 0:
        return {
            "snapshot_label": "broad_support_with_major_funds",
            "summary": (
                f"Current snapshot shows {holder_count} institutional holder(s), including "
                f"{major_fund_count} major fund(s) above the value threshold."
            ),
            "major_fund_count": major_fund_count,
        }

    return {
        "snapshot_label": "broad_support",
        "summary": (
            f"Current snapshot shows {holder_count} institutional holder(s), "
            f"which meets the size-aware confirmation threshold."
        ),
        "major_fund_count": 0,
    }


def _extract_holder_records(institutional_holders, ticker):
    if institutional_holders is None:
        return []

    if hasattr(institutional_holders, "empty") and institutional_holders.empty:
        return []

    records = []

    for raw_record in institutional_holders.to_dict(orient="records"):
        holder_name = raw_record.get("Holder") or raw_record.get("holder") or raw_record.get("name")
        if not holder_name:
            continue

        shares = raw_record.get("Shares") or raw_record.get("shares")
        raw_percent_out = raw_record.get("% Out") or raw_record.get("percent_out") or raw_record.get("percentOut")
        value = raw_record.get("Value") or raw_record.get("value")
        date_reported = raw_record.get("Date Reported") or raw_record.get("date_reported")

        percent_of_company = _format_percent(raw_percent_out)

        records.append(
            {
                "holder": holder_name,
                "shares": shares,
                "percent_of_company": percent_of_company,
                "value": value,
                "date_reported": date_reported,
                "summary_line": _build_summary_line(holder_name, ticker, percent_of_company, date_reported),
            }
        )

    return records


def check_13f(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
        market_cap = info.get("marketCap")
        company_size = _get_company_size(market_cap)

        institutional_holders = getattr(stock, "institutional_holders", None)
        shares_outstanding = info.get("sharesOutstanding")
        holder_records = _extract_holder_records(institutional_holders, ticker)

        if shares_outstanding:
            for record in holder_records:
                if record.get("percent_of_company") is None and record.get("shares"):
                    try:
                        record["percent_of_company"] = f"{(float(record['shares']) / float(shares_outstanding)) * 100:.2f}%"
                        record["summary_line"] = _build_summary_line(record["holder"], ticker, record["percent_of_company"], record.get("date_reported"))
                    except (TypeError, ValueError, ZeroDivisionError):
                        pass

        holder_count = len(holder_records)
        required_holders = _required_holders_for_size(company_size)
        top_funds = holder_records[:3]
        snapshot_summary = _format_snapshot_summary(company_size, holder_count, required_holders, top_funds)

        if holder_count >= required_holders:
            status = "confirmed"
            is_confirmed = True
        elif company_size == "small":
            status = "needs_to_be_validate"
            is_confirmed = False
        elif holder_count > 0:
            status = "needs_to_be_validate"
            is_confirmed = False
        else:
            status = "most_probably_no"
            is_confirmed = False

        return {
            "is_confirmed": is_confirmed,
            "status": status,
            "reason": _format_reason(company_size, holder_count, required_holders),
            "market_cap": market_cap,
            "shares_outstanding": shares_outstanding,
            "company_size": company_size,
            "institutional_holders_count": holder_count,
            "required_holders": required_holders,
            "top_funds": top_funds,
            "snapshot_label": snapshot_summary["snapshot_label"],
            "summary": snapshot_summary["summary"],
            "major_fund_count": snapshot_summary["major_fund_count"],
        }
    except Exception as exc:
        return {
            "is_confirmed": False,
            "status": "needs_to_be_validate",
            "reason": f"13F lookup unavailable for {ticker}: {exc}",
            "market_cap": None,
            "shares_outstanding": None,
            "company_size": "unknown",
            "institutional_holders_count": 0,
            "required_holders": 1,
            "top_funds": [],
            "snapshot_label": "unavailable",
            "summary": f"13F lookup unavailable for {ticker}: {exc}",
            "major_fund_count": 0,
        }


def is_13f_confirmed(ticker):
    return check_13f(ticker)["is_confirmed"]