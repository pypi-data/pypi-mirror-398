import os
import sys
import warnings

sys.path.insert(0, os.path.abspath("../rug"))

from rug import BarChart


def test_get_ratings():
    def do_test(symbol):
        bar = BarChart(symbol)
        ratings = bar.get_ratings()

        assert 4 == len(ratings)

        for rating in ratings:
            for status, values in rating.items():
                assert type(status) is str
                assert type(values) is dict

                assert "value" in values
                assert "percent" in values

    do_test("AMD")
    do_test("TSLA")
    do_test("AAPL")


def test_get_etf_basic_info():
    def do_test(symbol):
        keys = [
            "60_month_beta",
            "alpha",
            "asset_class",
            "asset_value",
            "brand",
            "description",
            "dividend",
            "dividends",
            "dividend_yield",
            "expense_ratio",
            "first_trade_price",
            "inception",
            "index_tracked",
            "last_dividend_date",
            "latest_dividend",
            "latest_split",
            "leverage",
            "managed_assets",
            "management_fee",
            "name",
            "options",
            "pe_ratio",
            "split_date",
            "std_dev",
            "description",
        ]

        data = BarChart(symbol).get_etf_basic_info()

        for key in data.keys():
            assert key in keys

        assert 10 < len(data.keys())

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        do_test("soxl")
        do_test("indy")
        do_test("arkb")
        do_test("TQQQ")
        do_test("vusa.l")
