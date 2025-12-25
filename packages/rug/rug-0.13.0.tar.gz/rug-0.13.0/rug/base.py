import logging
import re
from datetime import date, datetime
from html.parser import HTMLParser
from itertools import zip_longest

import cloudscraper
import requests
from requests.adapters import Retry

from .exceptions import HttpException

logging.basicConfig(level=logging.DEBUG)


class BaseAPI:
    req_retries = 4
    req_backoff_factor = 3
    timeout = 10
    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0"
    )

    def __init__(self, symbol=None):
        """
        Constructor.

        :param str symbol: Symbol of te item we wanna get info about.
        """

        if symbol:
            self.symbol = str(symbol)

    def get_session(self, use_cloudscraper=False):
        # Waits for 1.5s, 3s, 6s, 12s, 24s between requests.
        status_forcelist = (500, 502, 503, 504, 429)

        if use_cloudscraper:
            session = cloudscraper.create_scraper()
        else:
            retry = Retry(
                total=self.req_retries,
                read=self.req_retries,
                connect=self.req_retries,
                backoff_factor=self.req_backoff_factor,
                status_forcelist=status_forcelist,
            )
            session = requests.Session()
            session.adapters["http://"].max_retries = retry
            session.adapters["https://"].max_retries = retry

        return session

    def _get(self, *args, **kwargs):
        """
        Wraps https.get() method and raises custom exception
        in case of httpx expcetion.
        Also rises an exception for any non 2xx or 3xx status.
        """

        use_cloudscraper = kwargs.pop("use_cloudscraper", False)
        kwargs.setdefault("allow_redirects", True)
        kwargs.setdefault("timeout", self.timeout)

        try:
            response = self.get_session(use_cloudscraper).get(*args, **kwargs)
        except Exception as exc:
            raise HttpException(
                f"Couldn't perform GET request with args {args}"
            ) from exc

        response.raise_for_status()

        return response


class Data(dict):
    """
    Dict substitution which recursivelly handles
    non-existing keys.
    """

    def __getitem__(self, key):
        try:
            data = super().__getitem__(key)

            # If the data is dict we need to wrap it with
            # this class so it will carry this logic.
            if type(data) is dict:
                return self.__class__(data)

            # Data is not a dict so we return what we found.
            return data
        except Exception:
            # In case of non existing key we return empty self
            # which makes sure another direct key demand will
            # copy this logic.
            return self.__class__()


class HtmlTableParser(HTMLParser):
    """
    Parses out all data from the given table and
    casts them into ``datetime.date`` or ``float``.

    Parsed data can be retrieved with ``get_data()`` method.
    """

    def __init__(self, columns, *args, **kwargs):
        """
        Constructor.

        :param int columns: Number of columns the given table has.
        """

        self.data = []
        self.in_cell = False
        self.cell_data = ""
        self.columns = columns
        super().__init__(*args, **kwargs)

    def handle_starttag(self, tag, _attrs):
        if tag in ("td", "th"):
            self.in_cell = True

    def handle_endtag(self, tag: str):
        if tag in ("td", "th"):
            self.in_cell = False
            self.data.append(self.cell_data)
            self.cell_data = ""

    def handle_data(self, data):
        if self.in_cell:
            self.cell_data = self.parse_data(data)

    def parse_data(self, data):
        """
        Parses out all data from the given table and
        casts them into ``datetime.date`` or ``float``.
        """

        # logging.debug(f"data: {data}")

        # Date in YYYY-MM-DD format.
        if re.match(r"\d{4}-\d{2}-\d{2}", data):
            try:
                return date.fromisoformat(data)
            except Exception:
                pass

        # Date in MM-DD-YY where MM is short string
        # representation - like "May" or "Apr"
        if re.match(r"^[a-zA-Z]{3}-\d{2}-\d{2}$", data):
            try:
                return datetime.strptime(data, "%b-%d-%y").date()
            except Exception:
                pass

        # Date in MM/DD/YY format.
        if re.match(r"^\d{2}/\d{2}/\d{2}$", data):
            try:
                return datetime.strptime(data, "%m/%d/%y").date()
            except Exception:
                pass

        if "today" == data.lower():
            return date.today()

        # Dollars (positive or negative floats).
        if re.match(r"^\$[+-]?([0-9]*[.])?[0-9]+$", data):
            try:
                return float(data[1:])
            except Exception:
                pass

        # Int/float/percents (float or int with optional "%" sign as the last char).
        if re.match(r"^[0-9.,]+%?$", data):
            try:
                data = data.replace(",", "")
                return float(data[:-1] if "%" in data else data)
            except Exception:
                pass

        if "--" == data:
            return 0.0

        return data

    def get_data(self, sort_by=0):
        """
        Splits data into ``self.columns`` list of lists
        and returns them.
        Rows are sorted chronologically.

        :param int sort_by: Column index to sort by. Use `None` to skip sorting.
        :return: Parsed, casted table data as rows.
        :rtype: list
        """

        if not self.data:
            return []

        data = list(zip_longest(*[iter(self.data)] * self.columns, fillvalue=""))

        if sort_by is not None:
            sorted_data = sorted(
                data[1:],
                key=lambda row: row[sort_by],
            )
            sorted_data.insert(0, data[0])

            return sorted_data
        return data

    @staticmethod
    def fix_empty_cells(html):
        """
        Fixes impty <td> cells and will substitude them with "--"
        which later (see parse_dat()) gets recognized as 0.0 float.

        :param str html: HTML table to be fixed.
        :return: Fixed HTML.
        :rtype: str
        """
        return re.sub(r"<td([^>]*)><\/td>", "<td$1>--</td>", html, flags=re.DOTALL)


def strip_html_tags(text):
    """
    Removes HTML tags from the given string.

    :param str text: The string we want remove tags from.
    """

    return re.sub(r"<.*?>", "", text)


def calculate_perc_change(start, end):
    return (end - start) / start * 100
