from datetime import date

from rug import AlphaQuery


def test_get_eps():
    def do_test(symbol):
        aq = AlphaQuery(symbol)
        earnings = aq.get_eps()

        assert len(earnings) > 10

        for heading in earnings[0]:
            assert type(heading) is str

        for row in earnings[1:]:
            assert type(row[0]) is date
            assert type(row[1]) is date
            assert type(row[2]) is float
            assert type(row[3]) is float

    do_test("AMD")
    do_test("META")
    do_test("TSLA")
    do_test("NIO")


def test_get_revenues():
    def do_test(symbol):
        aq = AlphaQuery(symbol)
        revenues = aq.get_revenues()

        assert 10 <= len(revenues)

        for revenue in revenues:
            assert type(revenue[0]) is date
            assert type(revenue[1]) is float

    do_test("AMD")
    do_test("META")
    do_test("TSLA")
    do_test("NIO")


def test_get_earnings():
    def do_test(symbol):
        aq = AlphaQuery(symbol)
        earnings = aq.get_earnings()

        assert 10 <= len(earnings)

        for earning in earnings:
            assert type(earning[0]) is date
            assert type(earning[1]) is float

    do_test("AMD")
    do_test("META")
    do_test("TSLA")
    do_test("NIO")
