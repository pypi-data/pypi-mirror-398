# import os
# import sys
#
# import pytest
#
# sys.path.insert(0, os.path.abspath("../rug"))
#
# from rug import Yahoo
# from rug.exceptions import HttpException
#
#
# def test_get_current_price():
#     api = Yahoo("AAPL")
#     prices = api.get_current_price_change()
#
#     assert isinstance(prices, dict)
#     assert list(prices.keys()) == [
#         "pre_market",
#         "current_market",
#         "post_market",
#         "state",
#     ]
#     assert prices["state"] in ("pre-market", "post-market", "open")
#     assert list(prices["pre_market"].keys()) == ["change", "value"]
#     assert list(prices["pre_market"]["change"].keys()) == ["percents", "value"]
#     assert list(prices["current_market"].keys()) == ["change", "value"]
#     assert list(prices["current_market"]["change"].keys()) == ["percents", "value"]
#     assert list(prices["post_market"].keys()) == ["change", "value"]
#     assert list(prices["post_market"]["change"].keys()) == ["percents", "value"]
#
#
# def test_get_current_price_wrong_symbol():
#     api = Yahoo("AAPLL")
#
#     with pytest.raises(HttpException):
#         api.get_current_price_change()
