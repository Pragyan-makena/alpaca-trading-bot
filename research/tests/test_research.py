"""Unit tests for offline CSV validation and descriptive statistics."""
import unittest

import pandas as pd

from research.data.validate import normalize_price_frame
from research.metrics.summary import summarize_prices


class ValidateTests(unittest.TestCase):
    def test_adjusted_close_is_preferred_and_dates_are_sorted(self):
        raw = pd.DataFrame({
            "Date": ["2024-01-03", "2024-01-02"],
            "Close": [22.0, 20.0],
            "Adj Close": [11.0, 10.0],
        })
        frame, warnings, basis = normalize_price_frame(raw)
        self.assertEqual(basis, "Adj Close")
        self.assertEqual(frame["price"].tolist(), [10.0, 11.0])
        self.assertEqual(len(warnings), 0)

    def test_invalid_rows_and_duplicates_are_reported(self):
        raw = pd.DataFrame({
            "Date": ["2024-01-01", "bad-date", "2024-01-01", "2024-01-02"],
            "Close": [10.0, 11.0, 12.0, -1.0],
        })
        frame, warnings, _ = normalize_price_frame(raw)
        self.assertEqual(len(frame), 1)
        self.assertAlmostEqual(float(frame["price"].iloc[0]), 12.0)
        self.assertTrue(any("invalid dates" in warning for warning in warnings))
        self.assertTrue(any("non-positive prices" in warning for warning in warnings))
        self.assertTrue(any("duplicate date" in warning for warning in warnings))


class SummaryTests(unittest.TestCase):
    def test_known_price_series(self):
        index = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        frame = pd.DataFrame({"price": [100.0, 110.0, 99.0]}, index=index)
        result = summarize_prices(frame)
        self.assertAlmostEqual(result["price_change_pct"], -1.0)
        self.assertAlmostEqual(result["maximum_peak_to_trough_decline_pct"], -10.0)
        self.assertEqual(result["observations"], 3)


if __name__ == "__main__":
    unittest.main()
