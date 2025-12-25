import json
import re
from datetime import datetime

from .base import BaseAPI, HtmlTableParser
from .exceptions import DataException, SymbolNotFound


class AlphaQuery(BaseAPI):
    """
    AlphaQuery.com
    """

    def get_eps(self):
        """
        Returns eps for the given ``self.symbol`` as table rows
        (list of lists) where first row is table headers for comprehension.
        Rows are sorted chronologically.

        :raises SymbolNotFound: In case the page doesn't exist/returns error code or has no data.
        :raises DataException: In case data were found but are not in valid format - only one HTML table.
        :return: List of lists with earnings.
        :rtype: list
        """

        # Get HTML.
        try:
            html = self._get(
                f"https://www.alphaquery.com/stock/{self.symbol.upper()}/earnings-history",
                use_cloudscraper=True,
            )
        except Exception as e:
            raise SymbolNotFound from e

        finds = re.findall(r"<table.*?>.*?</table>", html.text, re.DOTALL)

        # Check if the HTML contains only one table.
        if 0 == len(finds):
            raise SymbolNotFound
        if 1 < len(finds):
            raise DataException(
                "More that one table found in HTML - don't know what to do now"
            )

        parser = HtmlTableParser(columns=4)
        parser.feed(finds[0])

        return parser.get_data()

    def get_revenues(self):
        """
        Returns revenues as time went in a list of tuples
        where first is a date and the second is revenue value.

        :raises SymbolNotFound: In case the page doesn't exist/returns error code or has no data.
        :raises DataException: In case data were found but are not JSON valid.
        :return: List of EPS including dates.
        :rtype: list
        """

        # 1. fetch data.
        json_data = self._get_chart_data(
            f"https://www.alphaquery.com/stock/{self.symbol.upper()}/fundamentals/quarterly/revenue"
        )

        # 2. process data.
        if json_data:
            return list(
                map(
                    lambda i: (
                        datetime.strptime(i["x"], "%Y-%m-%dT%H:%M:%SZ").date(),
                        float(i["value"] * 10_000_000 if i["value"] else 0.0),
                    ),
                    json_data,
                )
            )

        return []

    def get_earnings(self):
        """
        Returns earnings as time went in a list of tuples
        where first is a date and the second is earning value.

        :raises SymbolNotFound: In case the page doesn't exist/returns error code or has no data.
        :raises DataException: In case data were found but are not JSON valid.
        :return: List of earnings including dates.
        :rtype: list
        """

        # 1. fetch data.
        json_data = self._get_chart_data(
            f"https://www.alphaquery.com/stock/{self.symbol.upper()}/fundamentals/quarterly/normalized-income-after-taxes",
        )

        # 2. process data.
        if json_data:
            return list(
                map(
                    lambda i: (
                        datetime.strptime(i["x"], "%Y-%m-%dT%H:%M:%SZ").date(),
                        float(i["value"] * 10_000_000 if i["value"] else 0.0),
                    ),
                    json_data,
                )
            )

        return []

    def _get_chart_data(self, url):
        """
        Digs out data from Highcharts setup under
        the given URL.

        :param url str: URL we query for the data.
        :raises SymbolNotFound: In case the page doesn't exist/returns error code or has no data.
        :raises DataException: In case data were found but are not JSON valid.
        :return: Chart data - loaded JSON object.
        :rtype: any
        """

        try:
            response = self._get(url, use_cloudscraper=True)
        except Exception as e:
            raise SymbolNotFound from e

        finds = re.findall(
            r"var chartIndicatorData = (.+?)if", response.text, re.DOTALL
        )

        if not finds:
            raise SymbolNotFound

        try:
            return json.loads(finds[0])
        except Exception as e:
            raise DataException from e
