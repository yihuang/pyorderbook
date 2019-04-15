import pyximport; pyximport.install()
from orderbook import Order, BUY, SELL, Trade, OrderBook


def better_price(p1, p2, side):
    if side == BUY:
        return p1 <= p2
    else:
        return p1 >= p2


class Engine:
    def __init__(self):
        self.orderbook = OrderBook()
        self.orderbook.on_event = self.on_event
        self.trades = []
        self._next_order_id = 0
        self.all_orders = {}

    def next_order_id(self):
        n = self._next_order_id
        self._next_order_id += 1
        return n

    def limit_order(self, side, price, amount):
        o = Order(self.next_order_id(), side, price, amount)
        self.all_orders[o.id] = o
        self.orderbook.limit_order(o)
        self.validate()
        return o

    def cancel_order(self, orderid):
        o = self.orderbook.cancel_order(
            self.all_orders[orderid].price,
            orderid
        )
        self.validate()
        return o

    def on_event(self, name, evt):
        if name == 'trade':
            self.trades.append(evt)

    def validate(self):
        book = self.orderbook
        assert not book.bids or not book.asks or book.bids.max() < book.asks.min(), \
            'bids asks shouldn\'t cross'
        assert all(price == self.all_orders[makerid].price
                   for _, makerid, _, price in self.trades), \
            'trade price equals to maker price'
        assert all(better_price(price,
                                self.all_orders[takerid].price,
                                self.all_orders[takerid].side)
                   for takerid, _, _, price in self.trades), \
            'trade price equal or better than taker price'
        assert all(order.price == price
                   for price, lvl in book.levels.items()
                   for order in lvl.orders), \
            'level price is correct'
        assert all(sum(o.size for o in lvl.orders) == lvl.volume
                   for price, lvl in book.levels.items()), \
            'level volume is correct'


def test_simple():
    engine = Engine()
    book = engine.orderbook
    engine.limit_order(BUY, 100, 100)
    assert book.bids.min() == 100
    engine.limit_order(SELL, 100, 100)
    assert not book.bids

    engine.limit_order(SELL, 100, 100)
    assert book.asks.min() == 100
    engine.limit_order(BUY, 100, 100)
    assert not book.asks


def test_order():
    engine = Engine()
    engine.limit_order(BUY, 100, 100)
    engine.limit_order(BUY, 101, 100)
    engine.limit_order(BUY, 102, 100)
    engine.limit_order(SELL, 100, 150)
    assert engine.orderbook.bids.max() == 101
    assert engine.orderbook.levels[101].volume == 50


def test_depth():
    engine = Engine()
    book = engine.orderbook
    engine.limit_order(BUY, 100, 100)
    engine.limit_order(BUY, 100, 50)
    engine.limit_order(BUY, 101, 100)
    engine.limit_order(BUY, 102, 100)
    assert book.levels[100].volume == 150
    assert book.levels[101].volume == 100
    assert book.levels[102].volume == 100
    engine.limit_order(SELL, 100, 150)
    assert 102 not in book.levels
    assert book.levels[101].volume == 50


def test_trade_event():
    engine = Engine()
    engine.limit_order(BUY, 100, 100)
    engine.limit_order(BUY, 100, 50)
    o3 = engine.limit_order(BUY, 101, 100)
    o4 = engine.limit_order(BUY, 102, 100)
    o5 = engine.limit_order(SELL, 100, 150)

    assert tuple(engine.trades) == (
        (o5.id, o4.id, 100, 102),
        (o5.id, o3.id, 50, 101)
    )


def test_cancel():
    engine = Engine()
    book = engine.orderbook
    o = engine.limit_order(BUY, 100, 50)
    engine.cancel_order(o.id)
    assert not book.bids

    o = engine.limit_order(BUY, 100, 100)
    engine.limit_order(BUY, 101, 100)
    engine.cancel_order(o.id)
    assert book.bids.max() == 101
    assert book.levels[101].volume == 100
