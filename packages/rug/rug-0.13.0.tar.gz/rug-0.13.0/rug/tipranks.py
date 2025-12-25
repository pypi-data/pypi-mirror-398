from datetime import datetime

import requests

from .base import BaseAPI
from .exceptions import HttpException, SymbolNotFound


class TipRanks(BaseAPI):
    """
    Unofficial API wrapper class for TipRanks.com.
    Unofficial means this class calls some hidden endpoints
    and provides data that official API doesn't. Also doesn't
    need an authorization.
    """

    def get_dividends(self):
        """
        Fetches symbol dividends with following fields:

        - yield
        - amount
        - ex_date
        - payment_date
        - record_date
        - growth_since

        :return: List of dividend objects.
        :rtype: list
        """

        def download(url):
            try:
                response = self._get(url)
                response.raise_for_status()
            except requests.HTTPError as e:
                if e.response.status_code in (400, 404):
                    raise SymbolNotFound
                raise HttpException from e

            return response

        try:
            response = download(
                f"https://www.tipranks.com/stocks/{self.symbol.lower()}/stock-dividends/payload.json",
            )
            data = response.json()["models"]["stocks_dividends"][0]["list"]
        except IndexError:
            data = None
        except SymbolNotFound:
            response = download(
                f"https://tr-cdn.tipranks.com/assets/prod/etf/{self.symbol.lower()}/payload.json"
            )
            data = response.json()["dividends"]["history"]

        dividends = []

        if data:
            for item in data:
                dividends.append(
                    {
                        "yield": float(item["yield"] or 0) * 100,
                        "amount": float(item["amount"]),
                        "ex_date": (
                            datetime.strptime(
                                item["executionDate"], "%Y-%m-%dT%H:%M:%S.000Z"
                            ).date()
                            if item["executionDate"]
                            else None
                        ),
                        "payment_date": (
                            datetime.strptime(
                                item["payDate"], "%Y-%m-%dT%H:%M:%S.000Z"
                            ).date()
                            if item["payDate"]
                            else None
                        ),
                        "record_date": (
                            datetime.strptime(
                                item["recordDate"], "%Y-%m-%dT%H:%M:%S.000Z"
                            ).date()
                            if item["recordDate"]
                            else None
                        ),
                        "growth_since": (
                            datetime.strptime(
                                item["growthSince"], "%Y-%m-%dT%H:%M:%S.000Z"
                            )
                            if item["growthSince"]
                            else None
                        ),
                    }
                )

        return dividends

    def get_current_price_change(self):
        """
        Fetches current market price inc. pre/post market
        prices/percent/value changes. Also returns current
        market state (pre-market, open, post-market).

        Fetched stucture has following fields:

        - state (pre-market, open, post-market, closed)
        - pre_market
            - change
                - percents
                - value
            - value
        - current_market
            - change
                - percents
                - value
            - value
        - post_market
            - change
                - percents
                - value
            - value

        Values are floats (if present) or 0.0.
        Returned dict looks like:

        .. code-block:: python

            {
                "state": "open",
                "pre_market": {
                    "change": {
                        "percents": -1.32476,
                        "value": -1.42001
                    },
                    "value": 105.77
                },
                "current_market": {
                    "change": {
                        "percents": -1.6046284000000002,
                        "value": -1.7200012
                    },
                    "value": 105.47
                },
                "post_market": {
                    "change": {
                        "percents": 0.0,
                        "value": 0.0
                    },
                    "value": 0.0
                }
            }

        :return: Current/Pre/Post market numbers (all are floats).
        :rtype: dict
        """

        try:
            response = self._get(
                f"https://market.tipranks.com/api/quotes/GetQuotes?app_name=tr&tickers={self.symbol.upper()}"
            )
        except requests.HTTPError as e:
            raise HttpException from e

        try:
            data = response.json()["quotes"][0]
        except IndexError:
            raise SymbolNotFound

        output = {
            "state": "closed",
            "pre_market": {
                "change": {
                    "percents": 0.0,
                    "value": 0.0,
                },
                "value": 0.0,
            },
            "current_market": {
                "change": {
                    "percents": data["changePercent"],
                    "value": data["changeAmount"],
                },
                "value": data["price"],
            },
            "post_market": {"change": {"percents": 0.0, "value": 0.0}, "value": 0.0},
        }

        if data["isPremarket"]:
            output["pre_market"]["change"]["percents"] = data["prePostMarket"][
                "changePercent"
            ]
            output["pre_market"]["change"]["value"] = data["prePostMarket"][
                "changeAmount"
            ]
            output["pre_market"]["value"] = data["prePostMarket"]["price"]
            output["state"] = "pre-market"

        elif data["isAfterMarket"]:
            output["post_market"]["change"]["percents"] = data["prePostMarket"][
                "changePercent"
            ]
            output["post_market"]["change"]["value"] = data["prePostMarket"][
                "changeAmount"
            ]
            output["post_market"]["value"] = data["prePostMarket"]["price"]
            output["state"] = "post-market"

        elif data["isMarketOpen"]:
            output["state"] = "open"

        return output
