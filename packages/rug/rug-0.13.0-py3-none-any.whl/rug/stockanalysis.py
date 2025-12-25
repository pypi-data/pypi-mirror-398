import re
from datetime import datetime

import requests

from .base import BaseAPI, HtmlTableParser
from .exceptions import DataException, HttpException, SymbolNotFound


class StockAnalysis(BaseAPI):
    def get_basic_info(self):
        """
        Downloads basic info about symbol. Data are:

        - company_name
        - market
        - description
        - has_dividends
        - year_low
        - year_high
        - pe_ratio
        - eps
        - market_cap
        - 60_months_beta
        - upcoming_earnings_date
        - similar_items
            - name
            - market_cap
        """

        def download(url):
            try:
                response = self._get(url)
                response.raise_for_status()
            except requests.HTTPError as e:
                if 404 == e.response.status_code:
                    raise SymbolNotFound
                raise HttpException from e

            return response

        def download_financials_and_others():
            def download_financials(response):
                """
                Contributes with:
                - market_cap
                - eps
                - has_dividends
                - pe_ratio
                - 60_months_beta
                - upcoming_earnings_date
                """
                # Find all tables.
                finds = re.findall(
                    r"<table[^>]*>(.*?)</table>", response.text, re.DOTALL
                )

                if not finds:
                    raise DataException(
                        f"No basic data found for symbol {self.symbol}."
                    )

                # Parse 1st table.
                table = re.findall(r"<tbody>(.*?)</tbody>", finds[0], re.DOTALL)
                first_table_rows = []

                try:
                    parser = HtmlTableParser(2)
                    parser.feed(table[0])

                    first_table_rows = parser.get_data()
                except Exception as e:
                    raise DataException(
                        f"Invalid data in table for symbol {self.symbol}."
                    ) from e

                # Parse 2nd table.
                table = re.findall(r"<tbody>(.*?)</tbody>", finds[1], re.DOTALL)
                second_table_rows = []

                try:
                    parser = HtmlTableParser(2)
                    parser.feed(table[0])

                    second_table_rows = parser.get_data()
                except Exception as e:
                    raise DataException(
                        f"Invalid data in table for symbol {self.symbol}."
                    ) from e

                return {
                    "market_cap": first_table_rows[0][1],
                    "eps": first_table_rows[3][1],
                    "has_dividends": first_table_rows[2][1] != "n/a",
                    "pe_ratio": first_table_rows[7][1],
                    "60_months_beta": second_table_rows[3][1],
                    "upcoming_earnings_date": datetime.strptime(
                        second_table_rows[5][1], "%b %d, %Y"
                    ),
                }

            def download_company_name(response):
                """
                Contributes with:
                - company_name
                """
                try:
                    h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", response.text, re.DOTALL)
                    company_name = re.sub(r"\(.*?\)", "", h1[0]).strip()
                except Exception as e:
                    raise DataException(
                        f"Invalid data for company name for symobl {self.symbol}."
                    ) from e

                return {"company_name": company_name}

            def download_description(response):
                """
                Contributes with:
                - description
                """
                # For share
                try:
                    description = re.findall(
                        f"About {self.symbol.upper()}</h2>[^<]?<p>(.*?)</p>",
                        response.text,
                        re.DOTALL,
                    )[0]
                except Exception:
                    # For ETF
                    try:
                        description = re.findall(
                            f"About {self.symbol.upper()}</h2>.*?</div>[^<]<p>(.*?)</p>",
                            response.text,
                            re.DOTALL,
                        )[0]
                    except Exception as e:
                        raise DataException(
                            f"Invalid data for description for symbol {self.symbol}."
                        ) from e

                return {"description": description}

            # Try stocks data.
            response = download(
                f"https://stockanalysis.com/stocks/{self.symbol.lower()}/"
            )

            # Compile output.
            data = download_financials(response)
            data |= download_company_name(response)
            data |= download_description(response)

            return data

        def download_basics():
            response = download(
                f"https://stockanalysis.com/api/quotes/s/{self.symbol.lower()}"
            )

            try:
                data = response.json()
                data = data["data"]
            except Exception:
                raise DataException(f"Invalid JSON data for symbol {self.symbol}.")

            return {
                "market": data["ex"],
                "year_low": data["l52"],
                "year_high": data["h52"],
            }

        def similar_items():
            try:
                response = self._get(
                    f"https://stockanalysis.com/stocks/{self.symbol.lower()}/market-cap/"
                )
            except Exception:
                return {"similar_items": []}

            # Find all tables.
            finds = re.findall(r"<table[^>]*>(.*?)</table>", response.text, re.DOTALL)

            if not finds:
                raise DataException(f"No market cap found for symbol {self.symbol}.")

            # Parse 2nd table.
            finds = re.findall(r"<tbody>(.*?)</tbody>", finds[1], re.DOTALL)
            rows = []

            try:
                parser = HtmlTableParser(2)
                parser.feed(finds[0])

                rows = parser.get_data()
            except Exception as e:
                raise DataException(
                    f"Invalid data in table for symbol {self.symbol}."
                ) from e

            # Compile output.
            return {
                "similar_items": [
                    {"company_name": name, "market_cap": market_cap}
                    for name, market_cap in rows
                ]
            }

        data = download_basics()
        data |= download_financials_and_others()
        data |= similar_items()

        return data
