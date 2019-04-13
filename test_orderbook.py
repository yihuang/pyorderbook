from orderbook import Order, Side, Trade, OrderBook


class TestOrderBook(OrderBook):
    def __init__(self):
        super().__init__()
        self.trades = []

    def on_event(self, name, evt):
        if name == 'trade':
            self.trades.append(evt)


def test_simple():
    book = OrderBook()
    book.limit_order(Order(Side.BUY, 100, 100))
    assert book.bids[0].price == 100
    book.limit_order(Order(Side.SELL, 100, 100))
    assert not book.bids

    book.limit_order(Order(Side.SELL, 100, 100))
    assert book.asks[0].price == 100
    book.limit_order(Order(Side.BUY, 100, 100))
    assert not book.asks


def test_order():
    book = OrderBook()
    book.limit_order(Order(Side.BUY, 100, 100))
    book.limit_order(Order(Side.BUY, 101, 100))
    book.limit_order(Order(Side.BUY, 102, 100))
    book.limit_order(Order(Side.SELL, 100, 150))
    assert (book.bids[0].price, book.bids[0].size) == (101, 50)


def test_depth():
    book = OrderBook()
    book.limit_order(Order(Side.BUY, 100, 100))
    book.limit_order(Order(Side.BUY, 100, 50))
    book.limit_order(Order(Side.BUY, 101, 100))
    book.limit_order(Order(Side.BUY, 102, 100))
    assert book.depth[100] == 150
    assert book.depth[101] == 100
    assert book.depth[102] == 100
    book.limit_order(Order(Side.SELL, 100, 150))
    assert book.depth[102] == 0
    assert book.depth[101] == 50


def test_trade_event():
    book = TestOrderBook()
    book.limit_order(Order(Side.BUY, 100, 100))
    book.limit_order(Order(Side.BUY, 100, 50))
    book.limit_order(Order(Side.BUY, 101, 100))
    book.limit_order(Order(Side.BUY, 102, 100))
    book.limit_order(Order(Side.SELL, 100, 150))

    assert tuple(book.trades) == (
        Trade(5, 4, 100, 102),
        Trade(5, 3, 50, 101)
    )


def test_cancel():
    book = OrderBook()
    o = Order(Side.BUY, 100, 50)
    book.limit_order(o)
    book.cancel_order(o.id)
    assert not book.bids

    o = Order(Side.BUY, 100, 100)
    book.limit_order(o)
    book.limit_order(Order(Side.BUY, 101, 100))
    book.cancel_order(o.id)
    assert (book.bids[0].price, book.bids[0].size) == (101, 100)
