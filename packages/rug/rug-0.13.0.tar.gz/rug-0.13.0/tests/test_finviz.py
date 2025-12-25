import datetime

from rug import FinViz


def test_get_price_ratings():
    def do_test(symbol):
        fv = FinViz(symbol)
        ratings = fv.get_price_ratings()

        assert 0 < len(ratings)
        assert 5 == len(ratings[0])
        assert type(ratings[0][0]) is datetime.date
        assert type(ratings[0][1]) is str
        assert type(ratings[0][2]) is str
        assert type(ratings[0][3]) is str
        assert type(ratings[0][4]) in (str, float)

    do_test("AMD")
    do_test("META")
    do_test("TSLA")
    do_test("NIO")


def test_get_insider_trading():
    def do_test(symbol):
        fv = FinViz(symbol)
        trading = fv.get_insider_trading()

        assert 0 < len(trading)

        for row in trading:
            assert isinstance(row["person"], str)
            assert isinstance(row["relationship"], str)
            assert isinstance(row["date"], datetime.date)
            assert isinstance(row["transaction"], str)
            assert isinstance(row["price"], float)
            assert isinstance(row["amount"], int)

    do_test("AMD")
    do_test("TSLA")
    do_test("META")


def test_etf_holdings():
    def do_test(symbol, none_symbol=False):
        bar = FinViz(symbol)
        holdings = bar.get_etf_holdings()

        assert 10 == len(holdings)

        for holding in holdings:
            assert type(holding["name"]) is str

            if none_symbol:
                assert holding["symbol"] is None
            else:
                assert type(holding["symbol"]) is str

            assert type(holding["weight"]) is float

    do_test("SPLG")
    do_test("QQQ")
    do_test("TQQQ", True)
