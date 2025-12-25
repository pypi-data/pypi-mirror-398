# import pytest
#
# from rug import EtfDb
# from rug.exceptions import SymbolNotFound
#
#
# def test_get_basic_info():
#     def do_test(symbol):
#         data = EtfDb(symbol).get_basic_info()
#
#         for key in data.keys():
#             assert key in [
#                 "Issuer",
#                 "Brand",
#                 "Structure",
#                 "Expense Ratio",
#                 "Inception",
#                 "Index Tracked",
#                 "Category",
#                 "Leveraged",
#                 "Asset Class",
#                 "Asset Class Size",
#                 "Region (General)",
#                 "Region (Specific)",
#                 "Description",
#                 "Assets Under Management",
#                 "Year Low",
#                 "Year High",
#             ]
#
#     do_test("SPLG")
#     do_test("SPY")
#     do_test("TQQQ")
#
#     with pytest.raises(SymbolNotFound):
#         do_test("abcd")
#
#
# def test_get_holdings():
#     holdings = EtfDb("SPLG").get_holdings()
#     assert 15 == len(holdings)
#     assert "AAPL" in [h[0] for h in holdings]
#
#
# def test_get_etfs_by_item():
#     assert 25 == len(EtfDb("AAPL").get_etfs_by_item())
#
#     msft = EtfDb("MSFT").get_etfs_by_item()
#     assert 25 == len(msft)
#     assert str == type(msft[0][0])
#     assert str == type(msft[0][1])
#     assert str == type(msft[0][2])
#     assert float == type(msft[0][3])
#     assert float == type(msft[0][4])
#
#     with pytest.raises(SymbolNotFound):
#         EtfDb("MSFTTT").get_etfs_by_item()
