import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import form4
import form13f
import halal
import emailer
import sector_lookup
import main


class TestForm4Aggregation(unittest.TestCase):
    def test_aggregate_purchase_results_combines_same_company_and_ticker(self):
        results = [
            {
                "company": "Apple Inc.",
                "ticker": "AAPL",
                "insider": "Tim Cook",
                "amount": 1500.0,
                "sector": "Technology",
            },
            {
                "company": "Apple Inc.",
                "ticker": "AAPL",
                "insider": "Tim Cook",
                "amount": 2500.0,
                "sector": "Technology",
            },
            {
                "company": "Apple Inc.",
                "ticker": "AAPL",
                "insider": "Another Insider",
                "amount": 700.0,
                "sector": "Technology",
            },
        ]

        aggregated = form4.aggregate_purchase_results(results)

        self.assertEqual(len(aggregated), 1)

        apple = aggregated[0]
        self.assertEqual(apple["amount"], 4700.0)
        self.assertIn("Tim Cook", apple["insider"])
        self.assertIn("Another Insider", apple["insider"])


class TestMainPipeline(unittest.TestCase):
    def test_main_uses_realistic_alert_shape(self):
        realistic_data = [
            {
                "company": "Apple Inc.",
                "ticker": "AAPL",
                "insider": "Tim Cook",
                "amount": 125000.0,
                "sector": "Technology",
            },
            {
                "company": "Tesla, Inc.",
                "ticker": "TSLA",
                "insider": "Elon Musk",
                "amount": 50000.0,
                "sector": "Consumer Cyclical",
            },
            {
                "company": "Small Cap Co",
                "ticker": "SCPC",
                "insider": "Small Buyer",
                "amount": 1000.0,
                "sector": "Technology",
            },
        ]

        captured_output = io.StringIO()

        with patch.object(main, "get_form4_data", return_value=realistic_data), \
                                                 patch.object(main, "check_13f", side_effect=lambda ticker: {"is_confirmed": ticker == "AAPL", "status": "confirmed" if ticker == "AAPL" else "needs_to_be_validate", "reason": f"Checked {ticker}", "market_cap": 100000000000 if ticker == "AAPL" else 500000000, "company_size": "large" if ticker == "AAPL" else "small", "institutional_holders_count": 4 if ticker == "AAPL" else 0, "required_holders": 3 if ticker == "AAPL" else 1, "top_funds": [{"holder": "Vanguard", "summary_line": "Vanguard — Hold AAPL (0.42%) as of 2025-12-31", "shares": 1000000, "percent_of_company": "0.42%", "value": 100000000}], "snapshot_label": "broad_support_with_major_funds", "summary": "Current snapshot shows 4 institutional holder(s), including 1 major fund(s) above the value threshold.", "major_fund_count": 1}), \
               patch.object(main, "evaluate_halal", side_effect=lambda sector: {"is_halal": sector == "Technology", "status": "needs_to_be_validate" if sector == "Technology" else "most_probably_no", "reason": f"Checked {sector}"}), \
             patch.object(main, "send_email") as mock_send_email, \
             patch("sys.stdout", new=captured_output):
            main.main()

        mock_send_email.assert_called_once()
        subject, body = mock_send_email.call_args.args

        self.assertEqual(subject, "Stock Alert")
        self.assertIn("Needs to be Validate:", body)
        self.assertIn("Apple Inc. (AAPL)", body)
        self.assertIn("Total insider purchase amount: $125,000.00", body)
        self.assertIn("13F status: confirmed", body)
        self.assertIn("13F summary: Current snapshot shows 4 institutional holder(s), including 1 major fund(s) above the value threshold.", body)
        self.assertIn("13F note: Checked AAPL", body)
        self.assertIn("Top funds:", body)
        self.assertIn("Major funds detected: 1", body)
        self.assertIn("Vanguard — Hold AAPL (0.42%) as of 2025-12-31", body)
        self.assertIn("0.42%", body)
        self.assertIn("Insiders: Tim Cook", body)
        self.assertIn("Halal sector check: needs_to_be_validate", body)
        self.assertIn("Most Probably NO:", body)
        self.assertIn("Tesla, Inc. (TSLA)", body)
        self.assertIn("13F status: needs_to_be_validate", body)
        self.assertNotIn("Small Cap Co (SCPC)", body)

        stdout = captured_output.getvalue()
        self.assertIn("Starting script...", stdout)
        self.assertIn("Added to safe alerts", stdout)
        self.assertIn("Added to blocked alerts", stdout)


class TestHalalFiltering(unittest.TestCase):
    def test_evaluate_halal_rejects_known_haram_sector(self):
        decision = halal.evaluate_halal("Financial Services")
        self.assertFalse(decision["is_halal"])
        self.assertEqual(decision["status"], "most_probably_no")

    def test_evaluate_halal_accepts_safe_sector(self):
        decision = halal.evaluate_halal("Technology")
        self.assertTrue(decision["is_halal"])
        self.assertEqual(decision["status"], "needs_to_be_validate")

    def test_evaluate_halal_returns_unknown_for_missing_sector(self):
        decision = halal.evaluate_halal(None)
        self.assertFalse(decision["is_halal"])
        self.assertEqual(decision["status"], "most_probably_no")

    def test_is_halal_still_returns_boolean(self):
        self.assertTrue(halal.is_halal("Technology"))


class TestSectorLookup(unittest.TestCase):
    def test_get_sector_returns_sector_from_yfinance(self):
        mock_info = {"sector": "Technology"}

        with patch.object(sector_lookup.yf, "Ticker") as mock_ticker:
            mock_ticker.return_value.info = mock_info

            sector = sector_lookup.get_sector("AAPL")

        self.assertEqual(sector, "Technology")
        mock_ticker.assert_called_once_with("AAPL")

    def test_get_sector_returns_unknown_when_missing(self):
        with patch.object(sector_lookup.yf, "Ticker") as mock_ticker:
            mock_ticker.return_value.info = {}

            sector = sector_lookup.get_sector("AAPL")

        self.assertEqual(sector, "Unknown")


class TestForm13F(unittest.TestCase):
    def test_check_13f_uses_size_aware_thresholds(self):
        with patch.object(form13f.yf, "Ticker") as mock_ticker:
            mock_ticker.return_value.info = {"marketCap": 25_000_000_000}
            mock_ticker.return_value.institutional_holders = __import__("pandas").DataFrame(
                [
                    {"Holder": "Vanguard", "Shares": 1000000, "% Out": "0.42%", "Value": 100000000},
                    {"Holder": "BlackRock", "Shares": 800000, "% Out": "0.31%", "Value": 80000000},
                    {"Holder": "State Street", "Shares": 600000, "% Out": "0.24%", "Value": 60000000},
                    {"Holder": "Fidelity", "Shares": 400000, "% Out": "0.16%", "Value": 40000000},
                ]
            )

            decision = form13f.check_13f("AAPL")

        self.assertTrue(decision["is_confirmed"])
        self.assertEqual(decision["status"], "confirmed")
        self.assertEqual(decision["company_size"], "large")
        self.assertEqual(decision["required_holders"], 3)
        self.assertEqual(len(decision["top_funds"]), 3)
        self.assertEqual(decision["top_funds"][0]["holder"], "Vanguard")
        self.assertEqual(decision["top_funds"][0]["percent_of_company"], "0.42%")
        self.assertIn("Hold AAPL (0.42%)", decision["top_funds"][0]["summary_line"])
        self.assertEqual(decision["snapshot_label"], "broad_support_with_major_funds")
        self.assertIn("major fund(s)", decision["summary"])
        self.assertEqual(decision["major_fund_count"], 1)

    def test_check_13f_treats_small_caps_more_leniently(self):
        with patch.object(form13f.yf, "Ticker") as mock_ticker:
            mock_ticker.return_value.info = {"marketCap": 300_000_000}
            mock_ticker.return_value.institutional_holders = __import__("pandas").DataFrame([])

            decision = form13f.check_13f("SCPC")

        self.assertFalse(decision["is_confirmed"])
        self.assertEqual(decision["status"], "needs_to_be_validate")
        self.assertEqual(decision["company_size"], "small")
        self.assertEqual(decision["top_funds"], [])
        self.assertEqual(decision["snapshot_label"], "no_institutional_snapshot")


class TestEmailer(unittest.TestCase):
    def test_send_email_uses_gmail_smtp_with_expected_message(self):
        with patch.object(emailer, "EMAIL_USER", "tester@example.com"), \
             patch.object(emailer, "EMAIL_PASS", "secret-pass"), \
             patch.object(emailer.smtplib, "SMTP_SSL") as mock_smtp:

            server = mock_smtp.return_value.__enter__.return_value
            emailer.send_email("Stock Alert", "Body text")

        mock_smtp.assert_called_once_with("smtp.gmail.com", 465)
        server.login.assert_called_once_with("tester@example.com", "secret-pass")
        server.send_message.assert_called_once()

        message = server.send_message.call_args.args[0]
        self.assertEqual(message["Subject"], "Stock Alert")
        self.assertEqual(message["From"], "tester@example.com")
        self.assertEqual(message["To"], "tester@example.com")
        self.assertIn("Body text", message.get_payload())


if __name__ == "__main__":
    unittest.main()