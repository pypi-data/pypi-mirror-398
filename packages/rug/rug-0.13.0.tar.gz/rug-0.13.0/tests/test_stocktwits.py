import os
import sys

sys.path.insert(0, os.path.abspath("../rug"))

import time
from datetime import date, timedelta

from rug import StockTwits


def test_get_earnings_calendar():
    api = StockTwits()
    earnings = api.get_earnings_calendar(
        date.today(), date.today() + timedelta(days=12)
    )

    assert type(earnings) is list
    assert type(earnings[0]) is dict
    assert list(earnings[0].keys()) == ["date", "symbol", "time", "when"]
    assert type(earnings[0]["date"]) is date
    assert type(earnings[0]["time"]) is time.struct_time
