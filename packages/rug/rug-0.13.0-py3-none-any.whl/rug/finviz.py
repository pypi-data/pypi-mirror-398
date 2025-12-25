import re
from datetime import datetime

from .base import BaseAPI, HtmlTableParser
from .exceptions import DataException, SymbolNotFound


class FinViz(BaseAPI):
    """
    FinViz.com
    """

    def get_price_ratings(self):
        """
        Returns price ratings a.k.a price targets
        by analysts.

        Returned rows are:

        - date
        - status
        - analyst
        - rating
        - target price

        :return: Rows as a list of tuples where each tuple has 5 items.
        :rtype: list
        """

        try:
            html = self._get(
                f"https://finviz.com/quote.ashx?t={self.symbol.upper()}&ty=c&ta=1&p=d",
                headers={"User-Agent": self.user_agent},
            )
        except Exception as e:
            raise SymbolNotFound from e

        finds = re.findall(
            r"<table[^>]*js-table-ratings[^>]*>(.+?)</table>",
            html.text,
            re.DOTALL,
        )
        rows = []

        if finds:
            html = HtmlTableParser.fix_empty_cells(finds[0])
            parser = HtmlTableParser(columns=5)
            parser.feed(html)
            rows = parser.get_data()[1:]

        return rows

    def get_insider_trading(self):
        """
        Fetches insiders transactions (if available) as a
        list with following fields:

        - person
        - relationship
        - date
        - transaction
        - price
        - amount

        :return: Inriders transaction in reversed chronological order.
        :rtype: list
        """

        try:
            html = self._get(
                f"https://finviz.com/quote.ashx?t={self.symbol.upper()}&ty=c&ta=1&p=d",
                headers={"User-Agent": self.user_agent},
            )
        except Exception as e:
            raise SymbolNotFound from e

        rows = re.findall(r"<tr[^>]*insider-row*[^>]*>.+?<\/tr>", html.text, re.DOTALL)
        data = []

        if len(rows):
            parser = HtmlTableParser(columns=9)
            rows = "\n".join(rows)
            parser.feed(f"<table>{rows}</table>")

            for row in parser.get_data(sort_by=2):
                parsed_date = datetime.strptime(row[2], "%b %d '%y")
                data.append(
                    {
                        "person": row[0],
                        "relationship": row[1],
                        "date": parsed_date,
                        "transaction": row[3],
                        "price": float(row[4]),
                        "amount": int(row[5]),
                    }
                )

        return data

    def get_etf_holdings(self):
        """
        Fetches ETF holdings table as a list of dicts with following keys:

        - name
        - symbol (can be None)
        - instrument
        - weight (in %)
        """

        try:
            response = self._get(
                f"https://finviz.com/api/etf_holdings/{self.symbol.upper()}/top_ten",
                headers={"User-Agent": self.user_agent},
            )
        except Exception as e:
            raise SymbolNotFound from e

        try:
            data = response.json()
        except Exception as e:
            raise DataException from e

        to_return = []

        for i in data["rowData"]:
            to_return.append(
                {
                    "name": i["name"],
                    "symbol": i.get("ticker"),
                    "instrument": i["instrument"],
                    "weight": round(i["weight"] * 100, 2),
                }
            )

        return to_return
