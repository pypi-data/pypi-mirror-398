from .alphaquery import AlphaQuery
from .barchart import BarChart
from .finviz import FinViz
from .stockanalysis import StockAnalysis
from .stocktwits import StockTwits
from .tipranks import TipRanks


class Rug(
    AlphaQuery,
    BarChart,
    FinViz,
    StockAnalysis,
    StockTwits,
    TipRanks,
):
    """
    The Rug class provides a unified interface to all the functionality
    of the individual classes in the rug package.

    Use as:

    .. code-block:: python

        from rug import Rug

        Rug("AAPL").get_dividends()
    """

    def __init__(self, symbol=None):
        """
        Initializes the Rug object.

        :param str symbol: The stock symbol to work with.
        """
        super().__init__(symbol)
