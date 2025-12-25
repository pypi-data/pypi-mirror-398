# import copy
# import re
#
# from .base import BaseAPI, HtmlTableParser, strip_html_tags
# from .exceptions import DataException, SymbolNotFound
#
#
# class EtfDb(BaseAPI):
#     """
#     EtfDb.com
#     """
#
#     def get_basic_info(self):
#         """
#         Returns basic info about the given ETF. The info is:
#
#         - Issuer
#         - Brand
#         - Structure
#         - Expense Ratio
#         - Inception
#         - Index Tracked
#         - Category
#         - Leveraged
#         - Asset Class
#         - Asset Class Size
#         - Region (General)
#         - Region (Specific)
#         - Description
#         - Assets Under Management
#
#         :return: ETF basic info as a dict.
#         :rtype: dict
#         """
#
#         # Get HTML.
#         try:
#             html = self._get(
#                 f"https://etfdb.com/etf/{self.symbol.upper()}/#etf-ticker-profile"
#             )
#         except Exception as e:
#             raise SymbolNotFound from e
#
#         finds = re.findall(
#             r"class=\'ticker-assets\'.*?>(.*?)</div>[^<]*</div>", html.text, re.DOTALL
#         )
#
#         # Check if the HTML contains only two occurrences.
#         if 0 == len(finds):
#             raise SymbolNotFound
#         if 2 < len(finds):
#             raise DataException(
#                 "More that two occurrences found in HTML - don't know what to do now"
#             )
#
#         # Process 1st list.
#         list_items = re.findall(r"<span.*?>(.*?)</span>", finds[0], re.DOTALL)
#         list_items = [strip_html_tags(i) for i in list_items]
#         data = dict(zip(list_items[::2], list_items[1::2]))
#
#         # Process 2nd list.
#         list_items = re.findall(r"<span.*?>(.*?)</span>", finds[1], re.DOTALL)
#         list_items = [strip_html_tags(i) for i in list_items]
#         data |= dict(zip(list_items[::2], list_items[1::2]))
#
#         for key in copy.deepcopy(data).keys():
#             if key not in [
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
#             ]:
#                 del data[key]
#
#         # Fetch description.
#         finds = re.findall(
#             r"id='analyst-report'>.*?<p><p><p>(.+?)</p>", html.text, re.DOTALL
#         )
#
#         # Check if the HTML contains only ine occurrences.
#         if 0 == len(finds):
#             raise SymbolNotFound
#         if 1 < len(finds):
#             raise DataException(
#                 "More that one occurrences found in HTML - don't know what to do now"
#             )
#
#         data["Description"] = strip_html_tags(finds[0])
#
#         # ASM
#         finds = re.findall(
#             r"AUM</span>[^<]+<span[^>]+>([^<]+)</span>", html.text, re.DOTALL
#         )
#
#         # Check if the HTML contains only one occurrences.
#         if 0 == len(finds):
#             raise SymbolNotFound
#         if 1 < len(finds):
#             raise DataException(
#                 "More that one occurrences found in HTML - don't know what to do now"
#             )
#
#         data["Assets Under Management"] = finds[0]
#
#         # 52 week hi/low.
#         finds = re.findall(
#             r"52 Week Lo</span>[^<]+<span[^>]+>([^<]+)</span>", html.text, re.DOTALL
#         )
#
#         # Check if the HTML contains only one occurrences.
#         if 0 == len(finds):
#             raise SymbolNotFound
#         if 1 < len(finds):
#             raise DataException(
#                 "More that one occurrences found in HTML - don't know what to do now"
#             )
#
#         data["Year Low"] = finds[0]
#
#         finds = re.findall(
#             r"52 Week Hi</span>[^<]+<span[^>]+>([^<]+)</span>", html.text, re.DOTALL
#         )
#
#         # Check if the HTML contains only one occurrences.
#         if 0 == len(finds):
#             raise SymbolNotFound
#         if 1 < len(finds):
#             raise DataException(
#                 "More that one occurrences found in HTML - don't know what to do now"
#             )
#
#         data["Year High"] = finds[0]
#
#         return data
#
#     def get_holdings(self):
#         """
#         Returns ETF holdings (15 at max) list where each item is a list with items:
#
#         - symbol
#         - stock name
#         - percentage
#         """
#         try:
#             html = self._get(f"https://etfdb.com/etf/{self.symbol.upper()}/#holdings")
#         except Exception as e:
#             raise SymbolNotFound from e
#
#         finds = re.findall(
#             r"<table[^>]*etf-holdings[^>]*>(.*?)</table>", html.text, re.DOTALL
#         )
#
#         if not finds:
#             raise DataException("No holdings found.")
#
#         finds = re.findall(r"<tbody>(.*?)</tbody>", finds[0], re.DOTALL)
#         rows = []
#
#         if finds:
#             parser = HtmlTableParser(3)
#             parser.feed(finds[0])
#
#             rows = parser.get_data(sort_by=2)
#
#             return rows
#
#     def get_etfs_by_item(self):
#         """
#         Returns (top) 25 ETF's the item is included in
#         (sorted by it's weight).
#
#         Returned list contains of items where item is a list with items:
#
#         - symbol
#         - name
#         - category
#         - expense ratio
#         - weighting
#         """
#
#         try:
#             html = self._get(
#                 f"https://etfdb.com/stock/{self.symbol.upper()}/",
#                 follow_redirects=False,
#             )
#         except Exception as e:
#             raise SymbolNotFound from e
#
#         finds = re.findall(r"<table[^>]*>(.*?)</table>", html.text, re.DOTALL)
#
#         if not finds:
#             raise DataException("No ETFs found.")
#
#         finds = re.findall(r"<tbody>(.*?)</tbody>", finds[0], re.DOTALL)
#         rows = []
#
#         if finds:
#             parser = HtmlTableParser(5)
#             parser.feed(finds[0])
#
#             rows = parser.get_data()
#
#             return rows
