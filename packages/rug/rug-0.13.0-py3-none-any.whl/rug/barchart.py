import html
import json
import re
import warnings

from .base import BaseAPI, HtmlTableParser
from .exceptions import DataException, SymbolNotFound


class BarChart(BaseAPI):
    def get_ratings(self):
        """
        Returns ratings for past 4 months.
        Each months is a dict with status and it's values
        where values are in absolute number (number of analyst)
        and percents (ratio).

        Returns data in format:

        .. code-block:: json

            [
                {
                    "Strong Buy":{
                        "value":"14",
                        "percent":60.86956521739131
                    },
                    "Hold":{
                        "value":"9",
                        "percent":39.130434782608695
                    }
                },
                {
                    "Strong Buy":{
                        "value":"15",
                        "percent":65.21739130434783
                    },
                    "Hold":{
                        "value":"8",
                        "percent":34.78260869565217
                    }
                },
                {
                    "Strong Buy":{
                        "value":"15",
                        "percent":62.5
                    },
                    "Moderate Buy":{
                        "value":"1",
                        "percent":4.166666666666666
                    },
                    "Hold":{
                        "value":"8",
                        "percent":33.33333333333333
                    }
                },
                {
                    "Strong Buy":{
                        "value":"17",
                        "percent":73.91304347826086
                    },
                    "Moderate Buy":{
                        "value":"1",
                        "percent":4.3478260869565215
                    },
                    "Hold":{
                        "value":"5",
                        "percent":21.73913043478261
                    }
                }
            ]

        :raises SymbolNotFound: In case the page doesn't exist/returns error code.
        :return: List of each month data.
        :rtype: list
        """

        try:
            response = self._get(
                f"https://www.barchart.com/stocks/quotes/{self.symbol.upper()}/analyst-ratings",
                use_cloudscraper=True,
            )
        except Exception as e:
            raise SymbolNotFound from e

        finds = re.findall(
            r'<analyst-rating-pie[^>]*data-content="([^"]+)"',
            response.text,
            re.DOTALL,
        )

        if finds:
            return [json.loads(html.unescape(find)) for find in finds]

        return []

    def get_etf_basic_info(self):
        """
        Fetches ETF basic data including dividends. In case any record
        cannot be fetched it's still present but has ``None`` value or
        in case of dividends an emtpy list.
        Excetpion is description record where if not found an exception
        is raised.

        Returns data in format:

            .. code-block::

                {
                    '60_month_beta': 4.08,
                    'alpha': 18.2,
                    'asset_class': 'Equity',
                    'asset_value': 60.9,
                    'brand': 'Direxion Investments',
                    'description': 'The Direxion Daily Semiconductor Bull and Bear 3X Shares seek '
                                   'daily investment results, before fees and expenses, of 300% '
                                   'or 300% of the inverse (or opposite) of the performance of '
                                   'the PHLX Semiconductor Sector Index.',
                    'dividend': 0.28,
                    'dividend_yield': 0.46,
                    'dividends': [{'amount': 0.0077, 'date': datetime.date(2010, 9, 22)},
                                  {'amount': 0.0053, 'date': datetime.date(2014, 12, 23)},
                                  {'amount': 0.121, 'date': datetime.date(2017, 12, 19)},
                                  {'amount': 0.351, 'date': datetime.date(2018, 6, 19)},
                                  {'amount': 0.452, 'date': datetime.date(2018, 9, 25)},
                                  {'amount': 0.283, 'date': datetime.date(2018, 12, 27)},
                                  {'amount': 0.243, 'date': datetime.date(2019, 3, 19)},
                                  {'amount': 0.194, 'date': datetime.date(2019, 6, 25)},
                                  {'amount': 0.313, 'date': datetime.date(2019, 9, 24)},
                                  {'amount': 0.288, 'date': datetime.date(2019, 12, 23)},
                                  {'amount': 0.079, 'date': datetime.date(2020, 3, 24)},
                                  {'amount': 0.094, 'date': datetime.date(2020, 6, 23)},
                                  {'amount': 0.003, 'date': datetime.date(2020, 12, 22)},
                                  {'amount': 0.016, 'date': datetime.date(2021, 3, 23)},
                                  {'amount': 0.014, 'date': datetime.date(2021, 12, 21)},
                                  {'amount': 0.007, 'date': datetime.date(2022, 3, 22)},
                                  {'amount': 0.019, 'date': datetime.date(2022, 6, 22)},
                                  {'amount': 0.04, 'date': datetime.date(2022, 9, 20)},
                                  {'amount': 0.038, 'date': datetime.date(2022, 12, 20)},
                                  {'amount': 0.025, 'date': datetime.date(2023, 3, 21)},
                                  {'amount': 0.038, 'date': datetime.date(2023, 6, 21)},
                                  {'amount': 0.033, 'date': datetime.date(2023, 9, 19)},
                                  {'amount': 0.063, 'date': datetime.date(2023, 12, 21)},
                                  {'amount': 0.035, 'date': datetime.date(2024, 3, 19)},
                                  {'amount': 0.149, 'date': datetime.date(2024, 6, 25)}],
                    'expense_ratio': 0.9,
                    'first_trade_price': 9.64,
                    'inception': datetime.date(2010, 3, 11),
                    'index_tracked': 'PHLX Semiconductor Sector Index',
                    'last_dividend_date': datetime.date(2024, 6, 25),
                    'latest_dividend': 0.149,
                    'latest_split': '15-1',
                    'leverage': 'Triple-Long',
                    'managed_assets': '11,981,859.20 K',
                    'management_fee': 0.9,
                    'name': 'Direxion Daily Semiconductor Bull 3X Shares',
                    'options': True,
                    'pe_ratio': 0.03,
                    'split_date': datetime.date(2021, 3, 2),
                    'std_dev': 1.31
                }

        :return: Data as a dict with all the keys.
        :rtype: dict
        """

        def get(data, label, exact=False):
            """
            Tries to fetch row from the given data based on
            literal label mathing. Uses ``in`` operator by
            default but can be switched to precise ``==`` operator
            by ``exact=True`` parameter.

            In case of multiple rows matched an exception is raised.
            In case of no row is found a warning is raised and nothing is retured.

            :param list data: List of 2 sized tuples with label and value.
            :param str label: Label of the row we want to fetch.
            :param bool exact: Uses ``in`` operator if False ``==`` otherwise.
            :return: Found row value (if any).
            """

            found = []

            for i_label, value in data:
                if not exact and label.lower() in i_label.lower():
                    found.append(value)

                elif label.lower() == i_label.lower():
                    found.append(value)

            if 1 < len(found):
                raise Exception(
                    f"Label {label} was found more than once ({len(found)} times)."
                )
            if 0 == len(found):
                warnings.warn(f"Label {label} was not found - skipping")

                return

            return found[0]

        try:
            html = self._get(
                f"https://www.barchart.com/etfs-funds/quotes/{self.symbol.upper()}/profile",
                use_cloudscraper=True,
            )
        except Exception as e:
            raise SymbolNotFound from e

        # 1st table - overview
        finds = re.findall(r"<table>(.*?)</table>", html.text, re.DOTALL)

        if not finds:
            raise DataException("No basic data found.")

        parser = HtmlTableParser(2)
        parser.feed(finds[0])
        rows = parser.get_data()

        data = {
            "name": get(rows, "name"),
            "brand": get(rows, "fund family"),
            "inception": get(rows, "inception"),
            "index_tracked": get(rows, "underlying index"),
            "leverage": get(rows, "leverage"),
            "asset_class": get(rows, "asset class"),
        }

        # 2nd table - investment information
        parser = HtmlTableParser(2)
        parser.feed(finds[1])
        rows = parser.get_data()

        data |= {
            "alpha": get(rows, "alpha"),
            "60_month_beta": get(rows, "60-month beta"),
            "std_dev": float(dev) if (dev := get(rows, "standard deviation")) else None,
            "managed_assets": get(rows, "managed assets"),
            "asset_value": get(rows, "net asset value"),
            "first_trade_price": get(rows, "first trade"),
            "pe_ratio": get(rows, "p/e"),
            "management_fee": get(rows, "management fee"),
            "options": True if "yes" == (get(rows, "options") or "").lower() else False,
            "latest_dividend": get(rows, "latest dividend"),
            "last_dividend_date": get(rows, "last dividend date"),
            "dividend": get(rows, "annual dividend", exact=True),
            "dividend_yield": get(rows, "annual dividend yield"),
            "latest_split": get(rows, "latest split"),
            "split_date": get(rows, "split date"),
            "expense_ratio": get(rows, "expense ratio"),
        }

        # 3rd table - dividends
        if 3 == len(finds):
            parser = HtmlTableParser(2)
            parser.feed(finds[2])
            rows = parser.get_data()

            data |= {"dividends": [{"date": r[0], "amount": r[1]} for r in rows[1:]]}
        else:
            data["dividends"] = []

        # Description
        finds = re.findall(
            r"Description:(.*?)(?=<p>)<p>(.*?)</p>", html.text, re.DOTALL
        )

        if not finds:
            raise DataException("No description found.")

        data["description"] = finds[0][1]

        return data
