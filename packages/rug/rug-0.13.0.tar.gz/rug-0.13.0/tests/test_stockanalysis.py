import os
import sys

import pytest

sys.path.insert(0, os.path.abspath("../rug"))

from rug import StockAnalysis
from rug.exceptions import SymbolNotFound


def test_get_basic_info_stocks():
    def test(info):
        assert isinstance(info, dict)
        for key in [
            "company_name",
            "market",
            "description",
            "has_dividends",
            "year_low",
            "year_high",
            "pe_ratio",
            "eps",
            "market_cap",
            "60_months_beta",
            "upcoming_earnings_date",
            "similar_items",
        ]:
            assert key in info.keys()

        assert list(info["similar_items"][0].keys()) == [
            "company_name",
            "market_cap",
        ]

    test(StockAnalysis("AAPL").get_basic_info())
    test(StockAnalysis("BABA").get_basic_info())
    test(StockAnalysis("META").get_basic_info())


def test_get_basic_info_wrong_symbol():
    api = StockAnalysis("AAPLL")

    with pytest.raises(SymbolNotFound):
        api.get_basic_info()

    api = StockAnalysis("MEETA")

    with pytest.raises(SymbolNotFound):
        api.get_basic_info()
