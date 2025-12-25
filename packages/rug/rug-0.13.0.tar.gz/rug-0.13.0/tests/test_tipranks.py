import datetime
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath("../rug"))

from rug import TipRanks
from rug.exceptions import SymbolNotFound


def test_get_dividends():
    # Dividends
    api = TipRanks("AAPL")
    dividends = api.get_dividends()

    assert isinstance(dividends, list)
    assert list(dividends[0].keys()) == [
        "yield",
        "amount",
        "ex_date",
        "payment_date",
        "record_date",
        "growth_since",
    ]

    if dividends[0]["ex_date"]:
        assert isinstance(dividends[0]["ex_date"], datetime.date)

    if dividends[0]["payment_date"]:
        assert isinstance(dividends[0]["payment_date"], datetime.date)

    if dividends[0]["record_date"]:
        assert isinstance(dividends[0]["record_date"], datetime.date)

    if dividends[0]["growth_since"]:
        assert isinstance(dividends[0]["growth_since"], datetime.date)

    # No dividends.
    api = TipRanks("tsla")
    dividends = api.get_dividends()

    assert isinstance(dividends, list)
    assert dividends == []


def test_get_dividends_wrong_symbol():
    api = TipRanks("AAPLL")

    with pytest.raises(SymbolNotFound):
        api.get_dividends()
