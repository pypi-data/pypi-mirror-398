"""
ThetaData vs Yahoo Price Parity Tests

These tests verify that ThetaData split-adjusted prices match Yahoo Finance prices
within acceptable tolerance. Yahoo is considered the "gold standard" for split-adjusted
historical prices.

IMPORTANT: These tests require API credentials and make real API calls.
Run with: pytest tests/test_thetadata_yahoo_parity.py -v -m apitest

Test Matrix:
- GOOG: 20:1 split July 15, 2022
- AAPL: 4:1 split August 31, 2020
- TSLA: 3:1 split August 25, 2022

Created: 2025-12-11
Purpose: Ensure ThetaData and Yahoo produce comparable split-adjusted prices
"""

import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from unittest.mock import patch
import pytz

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

from lumibot.entities import Asset

# Check for ThetaData credentials
THETADATA_USERNAME = os.environ.get("THETADATA_USERNAME", "")
THETADATA_PASSWORD = os.environ.get("THETADATA_PASSWORD", "")
THETADATA_AVAILABLE = bool(THETADATA_USERNAME and THETADATA_PASSWORD)


# =============================================================================
# TEST CONFIGURATION
# =============================================================================

# Acceptable tolerance for price comparison (2%)
PRICE_TOLERANCE = 0.02

# Known splits for testing
SPLIT_TEST_CASES = [
    {
        "symbol": "GOOG",
        "split_date": date(2022, 7, 15),
        "split_ratio": 20,
        "test_date_before_split": date(2022, 7, 1),  # ~2 weeks before split
        "test_date_after_split": date(2022, 8, 1),   # ~2 weeks after split
    },
    {
        "symbol": "AAPL",
        "split_date": date(2020, 8, 31),
        "split_ratio": 4,
        "test_date_before_split": date(2020, 8, 15),  # ~2 weeks before split
        "test_date_after_split": date(2020, 9, 15),   # ~2 weeks after split
    },
    {
        "symbol": "TSLA",
        "split_date": date(2022, 8, 25),
        "split_ratio": 3,
        "test_date_before_split": date(2022, 8, 10),  # ~2 weeks before split
        "test_date_after_split": date(2022, 9, 10),   # ~2 weeks after split
    },
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_yahoo_price(symbol: str, target_date: date) -> float:
    """Get Yahoo Finance adjusted close price for a specific date"""
    if not YFINANCE_AVAILABLE:
        pytest.skip("yfinance not installed")

    start = target_date
    end = target_date + timedelta(days=5)  # Buffer for weekends

    ticker = yf.Ticker(symbol)
    hist = ticker.history(start=start.isoformat(), end=end.isoformat())

    if hist.empty:
        return None

    # Return the first available close price on or after target_date
    return float(hist["Close"].iloc[0])


def get_thetadata_price(symbol: str, target_date: date) -> float:
    """Get ThetaData split-adjusted close price for a specific date"""
    if not THETADATA_AVAILABLE:
        pytest.skip("ThetaData credentials not available")

    from lumibot.tools import thetadata_helper

    asset = Asset(symbol=symbol, asset_type="stock")
    quote_asset = Asset(symbol="USD", asset_type="forex")

    # Fetch data for a small range around the target date
    start_dt = datetime.combine(target_date - timedelta(days=5), datetime.min.time())
    end_dt = datetime.combine(target_date + timedelta(days=5), datetime.min.time())

    df = thetadata_helper.get_price_data(
        username=THETADATA_USERNAME,
        password=THETADATA_PASSWORD,
        asset=asset,
        start=start_dt,
        end=end_dt,
        timespan="day",
        quote_asset=quote_asset,
        datastyle="ohlc",
    )

    if df is None or df.empty:
        return None

    # Find the target date in the DataFrame
    target_str = target_date.isoformat()
    matching = df[df.index.date == target_date]

    if matching.empty:
        # Try the next available date
        future = df[df.index.date >= target_date]
        if future.empty:
            return None
        return float(future["close"].iloc[0])

    return float(matching["close"].iloc[0])


def calculate_price_difference_pct(price1: float, price2: float) -> float:
    """Calculate percentage difference between two prices"""
    if price1 is None or price2 is None:
        return None
    if price1 == 0:
        return None
    return abs(price1 - price2) / price1


# =============================================================================
# UNIT TESTS (No API calls - use mocked data)
# =============================================================================

class TestYahooPriceParityMocked:
    """Tests using mocked data - no API calls required"""

    def test_price_comparison_helper_works(self):
        """Test that our helper function calculates differences correctly"""
        assert calculate_price_difference_pct(100.0, 100.0) == 0.0
        assert calculate_price_difference_pct(100.0, 101.0) == pytest.approx(0.01)
        assert calculate_price_difference_pct(100.0, 102.0) == pytest.approx(0.02)
        assert calculate_price_difference_pct(100.0, 98.0) == pytest.approx(0.02)

    def test_tolerance_threshold_appropriate(self):
        """Test that our tolerance threshold is reasonable (2%)"""
        # 2% tolerance accounts for:
        # - Rounding differences between data providers
        # - Slight timing differences in price capture
        # - Minor data quality differences
        assert PRICE_TOLERANCE == 0.02

    @pytest.mark.parametrize("case", SPLIT_TEST_CASES, ids=lambda c: c["symbol"])
    def test_split_test_cases_are_valid(self, case):
        """Validate that our test case data is correct"""
        assert case["test_date_before_split"] < case["split_date"]
        assert case["test_date_after_split"] > case["split_date"]
        assert case["split_ratio"] > 1


# =============================================================================
# INTEGRATION TESTS (Real API calls - marked with @pytest.mark.apitest)
# =============================================================================

class TestYahooThetaDataParity:
    """
    Integration tests comparing ThetaData vs Yahoo prices.

    These tests make real API calls and require:
    - THETADATA_USERNAME and THETADATA_PASSWORD environment variables
    - yfinance package installed

    Run with: pytest -v -m apitest
    """

    @pytest.mark.apitest
    @pytest.mark.skipif(not YFINANCE_AVAILABLE, reason="yfinance not installed")
    @pytest.mark.skipif(not THETADATA_AVAILABLE, reason="ThetaData credentials not set")
    @pytest.mark.parametrize("case", SPLIT_TEST_CASES, ids=lambda c: c["symbol"])
    def test_price_matches_before_split(self, case):
        """
        Test: ThetaData and Yahoo prices should match BEFORE split dates.

        This verifies that ThetaData is correctly applying split adjustments
        to historical data before the split occurred.
        """
        symbol = case["symbol"]
        test_date = case["test_date_before_split"]

        yahoo_price = get_yahoo_price(symbol, test_date)
        theta_price = get_thetadata_price(symbol, test_date)

        if yahoo_price is None:
            pytest.skip(f"Yahoo price not available for {symbol} on {test_date}")
        if theta_price is None:
            pytest.skip(f"ThetaData price not available for {symbol} on {test_date}")

        diff_pct = calculate_price_difference_pct(yahoo_price, theta_price)

        assert diff_pct <= PRICE_TOLERANCE, (
            f"{symbol} price mismatch on {test_date} (before {case['split_ratio']}:1 split on {case['split_date']}): "
            f"Yahoo=${yahoo_price:.2f}, ThetaData=${theta_price:.2f}, diff={diff_pct:.2%}"
        )

    @pytest.mark.apitest
    @pytest.mark.skipif(not YFINANCE_AVAILABLE, reason="yfinance not installed")
    @pytest.mark.skipif(not THETADATA_AVAILABLE, reason="ThetaData credentials not set")
    @pytest.mark.parametrize("case", SPLIT_TEST_CASES, ids=lambda c: c["symbol"])
    def test_price_matches_after_split(self, case):
        """
        Test: ThetaData and Yahoo prices should match AFTER split dates.

        This is the easier case - both should return unadjusted post-split prices.
        """
        symbol = case["symbol"]
        test_date = case["test_date_after_split"]

        yahoo_price = get_yahoo_price(symbol, test_date)
        theta_price = get_thetadata_price(symbol, test_date)

        if yahoo_price is None:
            pytest.skip(f"Yahoo price not available for {symbol} on {test_date}")
        if theta_price is None:
            pytest.skip(f"ThetaData price not available for {symbol} on {test_date}")

        diff_pct = calculate_price_difference_pct(yahoo_price, theta_price)

        assert diff_pct <= PRICE_TOLERANCE, (
            f"{symbol} price mismatch on {test_date} (after {case['split_ratio']}:1 split on {case['split_date']}): "
            f"Yahoo=${yahoo_price:.2f}, ThetaData=${theta_price:.2f}, diff={diff_pct:.2%}"
        )

    @pytest.mark.apitest
    @pytest.mark.skipif(not YFINANCE_AVAILABLE, reason="yfinance not installed")
    @pytest.mark.skipif(not THETADATA_AVAILABLE, reason="ThetaData credentials not set")
    def test_goog_march_2020_covid_crash(self):
        """
        Test: GOOG price during COVID crash (March 2020) should match Yahoo.

        This is the specific scenario that triggered this testing effort.
        The GOOG 20:1 split in July 2022 must be applied retroactively to
        March 2020 data.
        """
        symbol = "GOOG"
        test_date = date(2020, 3, 23)  # Near the COVID crash bottom

        yahoo_price = get_yahoo_price(symbol, test_date)
        theta_price = get_thetadata_price(symbol, test_date)

        if yahoo_price is None:
            pytest.skip(f"Yahoo price not available for GOOG on {test_date}")
        if theta_price is None:
            pytest.skip(f"ThetaData price not available for GOOG on {test_date}")

        diff_pct = calculate_price_difference_pct(yahoo_price, theta_price)

        # This is the critical test - March 2020 data must reflect July 2022 split
        assert diff_pct <= PRICE_TOLERANCE, (
            f"GOOG March 2020 COVID crash price mismatch: "
            f"Yahoo=${yahoo_price:.2f}, ThetaData=${theta_price:.2f}, diff={diff_pct:.2%}. "
            f"This suggests the July 2022 20:1 split is not being applied correctly to historical data."
        )


# =============================================================================
# EXTENDED PARITY TESTS
# =============================================================================

class TestExtendedParity:
    """Extended tests for edge cases and longer date ranges"""

    @pytest.mark.apitest
    @pytest.mark.skipif(not YFINANCE_AVAILABLE, reason="yfinance not installed")
    @pytest.mark.skipif(not THETADATA_AVAILABLE, reason="ThetaData credentials not set")
    def test_spy_no_splits_parity(self):
        """
        Test: SPY (no recent splits) should match between Yahoo and ThetaData.

        This establishes a baseline that our comparison methodology works
        even for symbols without recent splits.
        """
        symbol = "SPY"
        test_date = date(2024, 6, 1)  # Recent date with no split

        yahoo_price = get_yahoo_price(symbol, test_date)
        theta_price = get_thetadata_price(symbol, test_date)

        if yahoo_price is None:
            pytest.skip(f"Yahoo price not available for SPY on {test_date}")
        if theta_price is None:
            pytest.skip(f"ThetaData price not available for SPY on {test_date}")

        diff_pct = calculate_price_difference_pct(yahoo_price, theta_price)

        assert diff_pct <= PRICE_TOLERANCE, (
            f"SPY price mismatch on {test_date}: "
            f"Yahoo=${yahoo_price:.2f}, ThetaData=${theta_price:.2f}, diff={diff_pct:.2%}"
        )

    @pytest.mark.apitest
    @pytest.mark.skipif(not YFINANCE_AVAILABLE, reason="yfinance not installed")
    @pytest.mark.skipif(not THETADATA_AVAILABLE, reason="ThetaData credentials not set")
    def test_multiple_dates_consistency(self):
        """
        Test: Multiple dates for the same symbol should all match within tolerance.

        This helps catch systematic errors in split adjustment.
        """
        symbol = "AAPL"
        test_dates = [
            date(2020, 1, 15),  # Before 2020 split
            date(2020, 6, 15),  # Before 2020 split
            date(2020, 9, 15),  # After 2020 split
            date(2021, 6, 15),  # After 2020 split
        ]

        mismatches = []

        for test_date in test_dates:
            yahoo_price = get_yahoo_price(symbol, test_date)
            theta_price = get_thetadata_price(symbol, test_date)

            if yahoo_price is None or theta_price is None:
                continue

            diff_pct = calculate_price_difference_pct(yahoo_price, theta_price)

            if diff_pct > PRICE_TOLERANCE:
                mismatches.append(
                    f"{test_date}: Yahoo=${yahoo_price:.2f}, ThetaData=${theta_price:.2f}, diff={diff_pct:.2%}"
                )

        assert len(mismatches) == 0, (
            f"AAPL price mismatches found:\n" + "\n".join(mismatches)
        )


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not apitest"])  # Run unit tests only by default
