import yfinance as yf


def get_sector(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        sector = info.get("sector")

        if sector:
            return sector

        return "Unknown"

    except Exception as e:
        print(f"Error looking up sector for {ticker}: {e}")
        return "Unknown"