"""
Comprehensive Option Strike Conversion Tests

Tests for _get_option_query_strike() function which converts split-adjusted strikes
back to original strikes for ThetaData API queries.

Created: 2025-12-12
Purpose: Verify strike conversion works correctly for:
- Forward splits (GOOG 20:1, AAPL 4:1, TSLA 5:1/3:1, NVDA 10:1)
- Reverse splits (GE 1:8, SIRI 1:10, SQQQ multiple)
- Fractional splits (GOOG 1.00275:1, GE 104:100)
- Leveraged ETF pairs (SQQQ/TQQQ opposite directions)
- Multi-split symbols (GE 10+ splits, AAPL 5+ splits)
- Boundary conditions (sim_date on split date, expiration on split date)

IMPORTANT: These tests require ThetaData API credentials.
Run with: THETADATA_USERNAME=xxx THETADATA_PASSWORD=xxx pytest tests/test_option_strike_conversion.py -v

Test Matrix (40 tests):
- Forward splits: 10 tests
- Reverse splits: 10 tests
- Fractional splits: 5 tests
- Leveraged ETF pairs: 5 tests
- Multi-split symbols: 5 tests
- Boundary & edge cases: 5 tests
"""

import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
import pytz

from lumibot.entities import Asset

# Check for ThetaData credentials
THETADATA_USERNAME = os.environ.get("THETADATA_USERNAME", "")
THETADATA_PASSWORD = os.environ.get("THETADATA_PASSWORD", "")
THETADATA_AVAILABLE = bool(THETADATA_USERNAME and THETADATA_PASSWORD)

# Import the function under test
try:
    from lumibot.tools.thetadata_helper import (
        _get_option_query_strike,
        _get_theta_splits,
        _normalize_split_events,
    )
    THETADATA_HELPER_AVAILABLE = True
except ImportError:
    THETADATA_HELPER_AVAILABLE = False


# =============================================================================
# TEST DATA: Known Stock Splits
# =============================================================================

# Forward splits (ratio > 1)
FORWARD_SPLITS = {
    "GOOG": [
        {"date": date(2022, 7, 15), "ratio": 20.0, "type": "20:1"},
        {"date": date(2015, 4, 27), "ratio": 1.00275, "type": "1.00275:1 (fractional)"},
        {"date": date(2014, 4, 3), "ratio": 2.0, "type": "2:1"},
    ],
    "AAPL": [
        {"date": date(2020, 8, 31), "ratio": 4.0, "type": "4:1"},
        {"date": date(2014, 6, 9), "ratio": 7.0, "type": "7:1"},
        {"date": date(2005, 2, 28), "ratio": 2.0, "type": "2:1"},
        {"date": date(2000, 6, 21), "ratio": 2.0, "type": "2:1"},
    ],
    "TSLA": [
        {"date": date(2022, 8, 25), "ratio": 3.0, "type": "3:1"},
        {"date": date(2020, 8, 31), "ratio": 5.0, "type": "5:1"},
    ],
    "NVDA": [
        {"date": date(2024, 6, 10), "ratio": 10.0, "type": "10:1"},
        {"date": date(2021, 7, 20), "ratio": 4.0, "type": "4:1"},
    ],
    "TQQQ": [
        {"date": date(2022, 1, 13), "ratio": 2.0, "type": "2:1"},
        {"date": date(2021, 1, 21), "ratio": 2.0, "type": "2:1"},
        {"date": date(2018, 5, 24), "ratio": 2.0, "type": "2:1"},
    ],
}

# Reverse splits (ratio < 1)
REVERSE_SPLITS = {
    "GE": [
        {"date": date(2021, 8, 2), "ratio": 0.125, "type": "1:8"},
    ],
    "SIRI": [
        {"date": date(2024, 9, 9), "ratio": 0.1, "type": "1:10"},
    ],
    "SQQQ": [
        {"date": date(2022, 9, 8), "ratio": 0.25, "type": "1:4"},
        {"date": date(2021, 8, 11), "ratio": 0.2, "type": "1:5"},
        {"date": date(2020, 8, 27), "ratio": 0.2, "type": "1:5"},
        {"date": date(2019, 9, 18), "ratio": 0.2, "type": "1:5"},
    ],
    "UVXY": [
        {"date": date(2024, 7, 11), "ratio": 0.1, "type": "1:10"},
        {"date": date(2023, 7, 13), "ratio": 0.1, "type": "1:10"},
        {"date": date(2022, 6, 29), "ratio": 0.1, "type": "1:10"},
    ],
}

# Fractional splits (non-integer ratios)
FRACTIONAL_SPLITS = {
    "GOOG": {"date": date(2015, 4, 27), "ratio": 1.00275, "type": "1.00275:1"},
    "GE_104_100": {"date": date(2019, 1, 1), "ratio": 1.04, "type": "104:100 (hypothetical)"},
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_option_asset(symbol: str, strike: float, expiration: date, right: str = "CALL") -> Asset:
    """Create an option Asset for testing"""
    return Asset(
        symbol=symbol,
        asset_type="option",
        strike=strike,
        expiration=expiration,
        right=right,
    )


def mock_splits_dataframe(splits_list: list) -> pd.DataFrame:
    """Create a mock splits DataFrame from a list of split dicts"""
    if not splits_list:
        return pd.DataFrame(columns=["event_date", "ratio", "numerator", "denominator"])

    records = []
    for split in splits_list:
        ratio = split["ratio"]
        # For forward splits, numerator > denominator (e.g., 20:1 means 20 new shares per 1 old)
        # For reverse splits, numerator < denominator (e.g., 1:8 means 1 new share per 8 old)
        if ratio > 1:
            numerator = ratio
            denominator = 1.0
        else:
            numerator = 1.0
            denominator = 1.0 / ratio

        records.append({
            "event_date": pd.Timestamp(split["date"]),
            "ratio": ratio,
            "numerator": numerator,
            "denominator": denominator,
        })

    return pd.DataFrame(records)


# =============================================================================
# FORWARD SPLIT TESTS (10 tests)
# =============================================================================

class TestForwardSplits:
    """Tests for forward splits (ratio > 1) like GOOG 20:1, AAPL 4:1"""

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_goog_20_1_split_march_2020_sim_date(self):
        """
        Test: GOOG option queried from March 2020 perspective

        Scenario: Strategy runs on March 23, 2020 (COVID crash) with GOOG options.
        The July 2022 20:1 split means a current $127.50 strike was originally $2550.

        Bug being tested: Date range should be March 2020 → Today, not Expiration → Today
        """
        # Current split-adjusted strike
        current_strike = 127.50
        # Expected original strike (pre-split): 127.50 * 20 = 2550
        expected_original = 2550.0

        option = create_option_asset(
            symbol="GOOG",
            strike=current_strike,
            expiration=date(2024, 7, 19),  # Future expiration
            right="CALL"
        )

        sim_datetime = datetime(2020, 3, 23, 9, 30, 0)  # COVID crash

        # Mock the split data
        goog_splits = [s for s in FORWARD_SPLITS["GOOG"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(goog_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01, (
            f"GOOG strike conversion failed: got ${result:.2f}, expected ${expected_original:.2f}"
        )

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_goog_20_1_split_day_before(self):
        """Test: sim_date = July 14, 2022 (day BEFORE 20:1 split)"""
        current_strike = 127.50
        expected_original = 2550.0  # Split hasn't happened yet, so must adjust

        option = create_option_asset("GOOG", current_strike, date(2024, 7, 19))
        sim_datetime = datetime(2022, 7, 14, 16, 0, 0)  # Day before split

        splits_after_sim = [s for s in FORWARD_SPLITS["GOOG"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(splits_after_sim)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_goog_20_1_split_day_of(self):
        """Test: sim_date = July 15, 2022 (split date)"""
        current_strike = 127.50
        # On split date, the split is effective, so no adjustment needed
        expected_original = 127.50

        option = create_option_asset("GOOG", current_strike, date(2024, 7, 19))
        sim_datetime = datetime(2022, 7, 15, 9, 30, 0)  # Split date

        # No splits after sim_date (the split is on sim_date, already reflected)
        splits_after_sim = [s for s in FORWARD_SPLITS["GOOG"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(splits_after_sim)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_goog_20_1_split_day_after(self):
        """Test: sim_date = July 16, 2022 (day AFTER split)"""
        current_strike = 127.50
        expected_original = 127.50  # Split already happened, no adjustment

        option = create_option_asset("GOOG", current_strike, date(2024, 7, 19))
        sim_datetime = datetime(2022, 7, 16, 9, 30, 0)  # Day after split

        splits_after_sim = [s for s in FORWARD_SPLITS["GOOG"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(splits_after_sim)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_aapl_4_1_split_jan_2020(self):
        """Test: AAPL 4:1 split (Aug 2020) from Jan 2020 perspective"""
        current_strike = 150.0
        expected_original = 600.0  # 150 * 4 = 600

        option = create_option_asset("AAPL", current_strike, date(2024, 6, 21))
        sim_datetime = datetime(2020, 1, 15, 9, 30, 0)

        aapl_splits = [s for s in FORWARD_SPLITS["AAPL"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(aapl_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_tsla_5_1_split_jan_2020(self):
        """Test: TSLA 5:1 split (Aug 2020) from Jan 2020 perspective"""
        current_strike = 200.0
        expected_original = 1000.0  # 200 * 5 = 1000

        option = create_option_asset("TSLA", current_strike, date(2024, 6, 21))
        sim_datetime = datetime(2020, 1, 15, 9, 30, 0)

        tsla_splits = [s for s in FORWARD_SPLITS["TSLA"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(tsla_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        # Should include both 5:1 (2020) and 3:1 (2022) = 15x
        expected_with_both = 200.0 * 5 * 3  # 3000
        assert abs(result - expected_with_both) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_tsla_3_1_split_july_2022(self):
        """Test: TSLA 3:1 split (Aug 2022) from July 2022 perspective"""
        current_strike = 200.0
        expected_original = 600.0  # 200 * 3 = 600 (only 3:1 split applies)

        option = create_option_asset("TSLA", current_strike, date(2024, 6, 21))
        sim_datetime = datetime(2022, 7, 15, 9, 30, 0)  # After 5:1, before 3:1

        tsla_splits = [s for s in FORWARD_SPLITS["TSLA"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(tsla_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_nvda_10_1_split_march_2024(self):
        """Test: NVDA 10:1 split (June 2024) from March 2024 perspective"""
        current_strike = 120.0
        expected_original = 1200.0  # 120 * 10 = 1200

        option = create_option_asset("NVDA", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2024, 3, 15, 9, 30, 0)

        nvda_splits = [s for s in FORWARD_SPLITS["NVDA"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(nvda_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_nvda_10_1_split_day_before(self):
        """Test: NVDA sim_date = June 9, 2024 (day before 10:1 split)"""
        current_strike = 120.0
        expected_original = 1200.0

        option = create_option_asset("NVDA", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2024, 6, 9, 16, 0, 0)

        nvda_splits = [s for s in FORWARD_SPLITS["NVDA"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(nvda_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_nvda_10_1_split_day_after(self):
        """Test: NVDA sim_date = June 11, 2024 (day after split)"""
        current_strike = 120.0
        expected_original = 120.0  # No adjustment needed

        option = create_option_asset("NVDA", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2024, 6, 11, 9, 30, 0)

        nvda_splits = [s for s in FORWARD_SPLITS["NVDA"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(nvda_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01


# =============================================================================
# REVERSE SPLIT TESTS (10 tests)
# =============================================================================

class TestReverseSplits:
    """Tests for reverse splits (ratio < 1) like GE 1:8, SIRI 1:10"""

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_ge_1_8_reverse_split_jan_2021(self):
        """
        Test: GE 1:8 reverse split (Aug 2021) from Jan 2021 perspective

        Reverse split means 8 old shares become 1 new share.
        Current $80 strike was originally $10 pre-reverse-split.
        Factor = 0.125, so original = 80 * 0.125 = 10
        """
        current_strike = 80.0
        expected_original = 10.0  # 80 * 0.125 = 10

        option = create_option_asset("GE", current_strike, date(2024, 6, 21))
        sim_datetime = datetime(2021, 1, 15, 9, 30, 0)

        ge_splits = [s for s in REVERSE_SPLITS["GE"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(ge_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01, (
            f"GE reverse split failed: got ${result:.2f}, expected ${expected_original:.2f}"
        )

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_ge_1_8_reverse_split_day_before(self):
        """Test: GE sim_date = Aug 1, 2021 (day before 1:8 reverse split)"""
        current_strike = 80.0
        expected_original = 10.0

        option = create_option_asset("GE", current_strike, date(2024, 6, 21))
        sim_datetime = datetime(2021, 8, 1, 16, 0, 0)

        ge_splits = [s for s in REVERSE_SPLITS["GE"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(ge_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_ge_1_8_reverse_split_day_after(self):
        """Test: GE sim_date = Aug 3, 2021 (day after reverse split)"""
        current_strike = 80.0
        expected_original = 80.0  # No adjustment needed

        option = create_option_asset("GE", current_strike, date(2024, 6, 21))
        sim_datetime = datetime(2021, 8, 3, 9, 30, 0)

        ge_splits = [s for s in REVERSE_SPLITS["GE"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(ge_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_siri_1_10_reverse_split_jan_2024(self):
        """Test: SIRI 1:10 reverse split (Sep 2024) from Jan 2024 perspective"""
        current_strike = 25.0
        expected_original = 2.50  # 25 * 0.1 = 2.50

        option = create_option_asset("SIRI", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2024, 1, 15, 9, 30, 0)

        siri_splits = [s for s in REVERSE_SPLITS["SIRI"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(siri_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_sqqq_1_4_reverse_split(self):
        """Test: SQQQ 1:4 reverse split (Sep 2022)"""
        current_strike = 40.0
        expected_original = 10.0  # 40 * 0.25 = 10

        option = create_option_asset("SQQQ", current_strike, date(2024, 6, 21))
        sim_datetime = datetime(2022, 9, 1, 9, 30, 0)  # Before Sep 8 split

        sqqq_splits = [s for s in REVERSE_SPLITS["SQQQ"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(sqqq_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_sqqq_1_5_reverse_split_2021(self):
        """Test: SQQQ 1:5 reverse split (Aug 2021)"""
        current_strike = 50.0
        expected_original = 10.0  # 50 * 0.2 = 10

        option = create_option_asset("SQQQ", current_strike, date(2021, 12, 17))
        sim_datetime = datetime(2021, 8, 1, 9, 30, 0)  # Before Aug 11 split

        # Only the Aug 2021 split applies here
        sqqq_splits = [s for s in REVERSE_SPLITS["SQQQ"]
                       if s["date"] > sim_datetime.date() and s["date"] < date(2022, 1, 1)]
        mock_df = mock_splits_dataframe(sqqq_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_sqqq_multiple_reverse_splits(self):
        """Test: SQQQ with multiple reverse splits applied cumulatively"""
        current_strike = 100.0
        # From 2019: 0.2 * 0.2 * 0.2 * 0.25 = 0.002
        # Original = 100 * 0.002 = 0.20
        expected_original = 0.20

        option = create_option_asset("SQQQ", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2019, 9, 1, 9, 30, 0)  # Before all 4 reverse splits

        sqqq_splits = [s for s in REVERSE_SPLITS["SQQQ"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(sqqq_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_uvxy_1_10_reverse_split_2024(self):
        """Test: UVXY 1:10 reverse split (July 2024)"""
        current_strike = 50.0
        expected_original = 5.0  # 50 * 0.1 = 5

        option = create_option_asset("UVXY", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2024, 7, 1, 9, 30, 0)

        uvxy_splits = [s for s in REVERSE_SPLITS["UVXY"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(uvxy_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_uvxy_multiple_reverse_splits(self):
        """Test: UVXY with 3 consecutive 1:10 reverse splits"""
        current_strike = 100.0
        # 0.1 * 0.1 * 0.1 = 0.001
        expected_original = 0.10  # 100 * 0.001 = 0.10

        option = create_option_asset("UVXY", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2022, 6, 1, 9, 30, 0)  # Before all 3 splits

        uvxy_splits = [s for s in REVERSE_SPLITS["UVXY"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(uvxy_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_siri_reverse_split_expiration_boundary(self):
        """Test: Reverse split with expiration BEFORE split date"""
        # Option expires Sep 6, 2024, split is Sep 9, 2024
        # From perspective of Jan 2024, the split is after both sim and expiration
        current_strike = 25.0
        expected_original = 2.50  # Still needs adjustment

        option = create_option_asset("SIRI", current_strike, date(2024, 9, 6))  # Expires before split
        sim_datetime = datetime(2024, 1, 15, 9, 30, 0)

        siri_splits = [s for s in REVERSE_SPLITS["SIRI"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(siri_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        # Even though option expires before split, we still query with adjusted strike
        assert abs(result - expected_original) < 0.01


# =============================================================================
# FRACTIONAL SPLIT TESTS (5 tests)
# =============================================================================

class TestFractionalSplits:
    """Tests for fractional/non-integer split ratios"""

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_goog_fractional_1_00275(self):
        """Test: GOOG 1.00275:1 fractional split (April 2015)"""
        current_strike = 100.0
        expected_original = 100.275  # 100 * 1.00275

        option = create_option_asset("GOOG", current_strike, date(2016, 6, 17))
        sim_datetime = datetime(2015, 4, 1, 9, 30, 0)  # Before April 27 split

        goog_fractional = [{"date": date(2015, 4, 27), "ratio": 1.00275}]
        mock_df = mock_splits_dataframe(goog_fractional)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_fractional_104_100(self):
        """Test: Hypothetical 104:100 (1.04) fractional split"""
        current_strike = 100.0
        expected_original = 104.0  # 100 * 1.04

        option = create_option_asset("TEST", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2019, 1, 1, 9, 30, 0)

        fractional_split = [{"date": date(2020, 6, 15), "ratio": 1.04}]
        mock_df = mock_splits_dataframe(fractional_split)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_fractional_1281_1000(self):
        """Test: GE-style 1281:1000 (1.281) fractional split"""
        current_strike = 100.0
        expected_original = 128.1  # 100 * 1.281

        option = create_option_asset("TEST", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2019, 1, 1, 9, 30, 0)

        fractional_split = [{"date": date(2020, 6, 15), "ratio": 1.281}]
        mock_df = mock_splits_dataframe(fractional_split)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_cumulative_fractional_splits(self):
        """Test: Multiple fractional splits applied cumulatively"""
        current_strike = 100.0
        # 1.04 * 1.02 * 1.01 = 1.071408
        expected_original = 107.1408

        option = create_option_asset("TEST", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2018, 1, 1, 9, 30, 0)

        fractional_splits = [
            {"date": date(2019, 3, 15), "ratio": 1.04},
            {"date": date(2020, 6, 15), "ratio": 1.02},
            {"date": date(2021, 9, 15), "ratio": 1.01},
        ]
        mock_df = mock_splits_dataframe(fractional_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_very_small_fractional(self):
        """Test: Very small fractional split (1.001)"""
        current_strike = 1000.0
        expected_original = 1001.0  # 1000 * 1.001

        option = create_option_asset("TEST", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2020, 1, 1, 9, 30, 0)

        small_fractional = [{"date": date(2021, 6, 15), "ratio": 1.001}]
        mock_df = mock_splits_dataframe(small_fractional)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01


# =============================================================================
# LEVERAGED ETF PAIR TESTS (5 tests)
# =============================================================================

class TestLeveragedETFPairs:
    """Tests for leveraged ETF pairs with opposite split directions"""

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_tqqq_vs_sqqq_same_date_opposite(self):
        """
        Test: TQQQ 2:1 (forward) vs SQQQ 1:4 (reverse) on same date

        Jan 13, 2022: TQQQ did 2:1 forward split
        Sep 8, 2022: SQQQ did 1:4 reverse split

        These are opposite directions - verify both work correctly.
        """
        # TQQQ forward split
        tqqq_strike = 50.0
        tqqq_expected = 100.0  # 50 * 2 = 100

        tqqq_option = create_option_asset("TQQQ", tqqq_strike, date(2024, 6, 21))
        tqqq_sim = datetime(2022, 1, 1, 9, 30, 0)

        tqqq_splits = [{"date": date(2022, 1, 13), "ratio": 2.0}]
        tqqq_mock = mock_splits_dataframe(tqqq_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=tqqq_mock):
            tqqq_result = _get_option_query_strike(tqqq_option, sim_datetime=tqqq_sim)

        assert abs(tqqq_result - tqqq_expected) < 0.01, f"TQQQ: got {tqqq_result}, expected {tqqq_expected}"

        # SQQQ reverse split
        sqqq_strike = 40.0
        sqqq_expected = 10.0  # 40 * 0.25 = 10

        sqqq_option = create_option_asset("SQQQ", sqqq_strike, date(2024, 6, 21))
        sqqq_sim = datetime(2022, 9, 1, 9, 30, 0)

        sqqq_splits = [{"date": date(2022, 9, 8), "ratio": 0.25}]
        sqqq_mock = mock_splits_dataframe(sqqq_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=sqqq_mock):
            sqqq_result = _get_option_query_strike(sqqq_option, sim_datetime=sqqq_sim)

        assert abs(sqqq_result - sqqq_expected) < 0.01, f"SQQQ: got {sqqq_result}, expected {sqqq_expected}"

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_tqqq_2_1_forward_split(self):
        """Test: TQQQ 2:1 forward split (Jan 2022)"""
        current_strike = 50.0
        expected_original = 100.0

        option = create_option_asset("TQQQ", current_strike, date(2024, 6, 21))
        sim_datetime = datetime(2022, 1, 1, 9, 30, 0)

        tqqq_splits = [s for s in FORWARD_SPLITS["TQQQ"] if s["date"] > sim_datetime.date()]
        mock_df = mock_splits_dataframe(tqqq_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_sqqq_reverse_same_period(self):
        """Test: SQQQ reverse split in same period as TQQQ forward"""
        current_strike = 40.0
        expected_original = 10.0

        option = create_option_asset("SQQQ", current_strike, date(2024, 6, 21))
        sim_datetime = datetime(2022, 9, 1, 9, 30, 0)

        sqqq_splits = [{"date": date(2022, 9, 8), "ratio": 0.25}]
        mock_df = mock_splits_dataframe(sqqq_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_leveraged_etf_high_strike_pre_reverse(self):
        """Test: High strike price before reverse split"""
        # UVXY could have had strikes > $1000 before multiple reverse splits
        current_strike = 1000.0
        # With 3x 1:10 reverse splits: 0.001 cumulative
        expected_original = 1.0  # 1000 * 0.001 = 1

        option = create_option_asset("UVXY", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2022, 6, 1, 9, 30, 0)

        uvxy_splits = REVERSE_SPLITS["UVXY"]
        mock_df = mock_splits_dataframe(uvxy_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_leveraged_etf_low_strike_post_reverse(self):
        """Test: Low strike price after reverse split (no adjustment)"""
        current_strike = 8.0
        expected_original = 8.0  # No adjustment needed, sim after all splits

        option = create_option_asset("UVXY", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2024, 8, 1, 9, 30, 0)  # After July 2024 split

        # No splits after sim_datetime
        mock_df = mock_splits_dataframe([])

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01


# =============================================================================
# MULTI-SPLIT SYMBOL TESTS (5 tests)
# =============================================================================

class TestMultiSplitSymbols:
    """Tests for symbols with multiple splits over time"""

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_aapl_all_splits_cumulative(self):
        """Test: AAPL with multiple splits (4:1 2020, 7:1 2014, 2:1 2005, 2:1 2000)"""
        current_strike = 150.0
        # From 1999: 4 * 7 * 2 * 2 = 112x cumulative
        # Original = 150 * 112 = 16800
        expected_original = 16800.0

        option = create_option_asset("AAPL", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(1999, 1, 1, 9, 30, 0)

        aapl_splits = FORWARD_SPLITS["AAPL"]
        mock_df = mock_splits_dataframe(aapl_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 1.0  # Allow for rounding

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_tsla_5_1_plus_3_1_cumulative(self):
        """Test: TSLA 5:1 (2020) + 3:1 (2022) = 15x cumulative"""
        current_strike = 200.0
        expected_original = 3000.0  # 200 * 15 = 3000

        option = create_option_asset("TSLA", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2020, 1, 1, 9, 30, 0)

        tsla_splits = FORWARD_SPLITS["TSLA"]
        mock_df = mock_splits_dataframe(tsla_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_nvda_multiple_splits(self):
        """Test: NVDA 10:1 (2024) + 4:1 (2021) = 40x cumulative"""
        current_strike = 120.0
        expected_original = 4800.0  # 120 * 40 = 4800

        option = create_option_asset("NVDA", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2021, 1, 1, 9, 30, 0)

        nvda_splits = FORWARD_SPLITS["NVDA"]
        mock_df = mock_splits_dataframe(nvda_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_sqqq_all_reverse_splits_cumulative(self):
        """Test: SQQQ with all 4 reverse splits"""
        current_strike = 100.0
        # 0.25 * 0.2 * 0.2 * 0.2 = 0.002
        expected_original = 0.20

        option = create_option_asset("SQQQ", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2019, 1, 1, 9, 30, 0)

        sqqq_splits = REVERSE_SPLITS["SQQQ"]
        mock_df = mock_splits_dataframe(sqqq_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_cumulative_factor_precision(self):
        """Test: Verify cumulative factor maintains precision with many splits"""
        current_strike = 100.0
        # 10 splits of 1.1 each: 1.1^10 = 2.5937424601
        expected_original = 259.37424601

        option = create_option_asset("TEST", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2010, 1, 1, 9, 30, 0)

        many_splits = [
            {"date": date(2011, 1, 1), "ratio": 1.1},
            {"date": date(2012, 1, 1), "ratio": 1.1},
            {"date": date(2013, 1, 1), "ratio": 1.1},
            {"date": date(2014, 1, 1), "ratio": 1.1},
            {"date": date(2015, 1, 1), "ratio": 1.1},
            {"date": date(2016, 1, 1), "ratio": 1.1},
            {"date": date(2017, 1, 1), "ratio": 1.1},
            {"date": date(2018, 1, 1), "ratio": 1.1},
            {"date": date(2019, 1, 1), "ratio": 1.1},
            {"date": date(2020, 1, 1), "ratio": 1.1},
        ]
        mock_df = mock_splits_dataframe(many_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01


# =============================================================================
# BOUNDARY & EDGE CASE TESTS (5 tests)
# =============================================================================

class TestBoundaryAndEdgeCases:
    """Tests for boundary conditions and edge cases"""

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_sim_datetime_none_default_behavior(self):
        """Test: sim_datetime=None should use expiration date as fallback"""
        current_strike = 127.50

        option = create_option_asset("GOOG", current_strike, date(2025, 6, 20))

        # No sim_datetime, so should use expiration date
        # Expiration is June 2025, split was July 2022, so no adjustment needed
        goog_splits = []  # No splits after June 2025
        mock_df = mock_splits_dataframe(goog_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=None)

        assert abs(result - current_strike) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_sim_datetime_exactly_on_split_date_midnight(self):
        """Test: sim_datetime exactly at midnight on split date"""
        current_strike = 127.50
        # Split is on July 15, 2022. At midnight that day, split should be in effect.
        expected_original = 127.50  # No adjustment (split already happened)

        option = create_option_asset("GOOG", current_strike, date(2024, 7, 19))
        sim_datetime = datetime(2022, 7, 15, 0, 0, 0)  # Midnight on split date

        # Split is on sim_date, so it shouldn't be in "future" splits
        splits_after = [{"date": date(2022, 7, 15), "ratio": 20.0}]
        mock_df = mock_splits_dataframe(splits_after)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        # Depending on implementation, this could include or exclude the split
        # Current implementation uses > comparison, so split on same date is excluded
        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_expiration_exactly_on_split_date(self):
        """Test: Option expiration falls exactly on split date"""
        current_strike = 127.50

        # Option expires on split date (July 15, 2022)
        # From March 2020 perspective, need to adjust
        expected_original = 2550.0  # 127.50 * 20

        option = create_option_asset("GOOG", current_strike, date(2022, 7, 15))  # Expires on split date
        sim_datetime = datetime(2020, 3, 23, 9, 30, 0)

        goog_splits = [{"date": date(2022, 7, 15), "ratio": 20.0}]
        mock_df = mock_splits_dataframe(goog_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_strike_zero_edge_case(self):
        """Test: Strike of 0 (edge case)"""
        current_strike = 0.0
        expected_original = 0.0  # 0 * anything = 0

        option = create_option_asset("GOOG", current_strike, date(2024, 7, 19))
        sim_datetime = datetime(2020, 3, 23, 9, 30, 0)

        goog_splits = [{"date": date(2022, 7, 15), "ratio": 20.0}]
        mock_df = mock_splits_dataframe(goog_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert result == 0.0

    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_very_large_strike(self):
        """Test: Very large strike price ($10,000+)"""
        current_strike = 10000.0
        # GOOG 20:1 split
        expected_original = 200000.0  # 10000 * 20

        option = create_option_asset("GOOG", current_strike, date(2024, 7, 19))
        sim_datetime = datetime(2020, 3, 23, 9, 30, 0)

        goog_splits = [{"date": date(2022, 7, 15), "ratio": 20.0}]
        mock_df = mock_splits_dataframe(goog_splits)

        with patch("lumibot.tools.thetadata_helper._get_theta_splits", return_value=mock_df):
            result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        assert abs(result - expected_original) < 0.01


# =============================================================================
# INTEGRATION TESTS (Real API calls)
# =============================================================================

@pytest.mark.apitest
class TestIntegrationWithRealAPI:
    """
    Integration tests that make real ThetaData API calls.

    Run with: THETADATA_USERNAME=xxx THETADATA_PASSWORD=xxx pytest -v -m apitest
    """

    @pytest.mark.skipif(not THETADATA_AVAILABLE, reason="ThetaData credentials not set")
    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_goog_real_split_data(self):
        """Test: Fetch real GOOG split data from ThetaData"""
        underlying = Asset(symbol="GOOG", asset_type="stock")

        # Fetch splits from 2020 to now
        splits = _get_theta_splits(underlying, date(2020, 1, 1), date.today())

        assert splits is not None, "Failed to fetch GOOG splits"

        if not splits.empty:
            # Verify July 2022 20:1 split is present
            july_2022_split = splits[
                (splits["event_date"].dt.year == 2022) &
                (splits["event_date"].dt.month == 7)
            ]
            assert not july_2022_split.empty, "GOOG July 2022 split not found"

    @pytest.mark.skipif(not THETADATA_AVAILABLE, reason="ThetaData credentials not set")
    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_aapl_real_split_data(self):
        """Test: Fetch real AAPL split data from ThetaData"""
        underlying = Asset(symbol="AAPL", asset_type="stock")

        splits = _get_theta_splits(underlying, date(2020, 1, 1), date.today())

        assert splits is not None, "Failed to fetch AAPL splits"

        if not splits.empty:
            # Verify Aug 2020 4:1 split is present
            aug_2020_split = splits[
                (splits["event_date"].dt.year == 2020) &
                (splits["event_date"].dt.month == 8)
            ]
            assert not aug_2020_split.empty, "AAPL Aug 2020 split not found"

    @pytest.mark.skipif(not THETADATA_AVAILABLE, reason="ThetaData credentials not set")
    @pytest.mark.skipif(not THETADATA_HELPER_AVAILABLE, reason="thetadata_helper not available")
    def test_goog_option_strike_conversion_real(self):
        """Test: Real GOOG option strike conversion with actual split data"""
        current_strike = 175.0  # Current split-adjusted strike

        option = create_option_asset("GOOG", current_strike, date(2025, 6, 20))
        sim_datetime = datetime(2020, 3, 23, 9, 30, 0)  # COVID crash

        # Use real API - no mocking
        result = _get_option_query_strike(option, sim_datetime=sim_datetime)

        # Should be approximately 175 * 20 = 3500 (accounting for 20:1 split)
        # Allow some tolerance for fractional splits
        assert 3000 < result < 4000, (
            f"GOOG strike conversion unexpected: ${result:.2f}, expected ~$3500"
        )


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not apitest"])  # Run unit tests only by default
