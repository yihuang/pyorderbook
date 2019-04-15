import time
from enum import IntEnum
from typing import NamedTuple
from pyroaring import BitMap

from decimal import Decimal


OrderId = int
Price = int


class Side(IntEnum):
    BUY = 0
    SELL = 1


class Order:
    __slots__ = ('id', 'price', 'original_size', 'size', 'side', 'order_time')

    def __init__(self, id: OrderId, side: Side, price: Price, size: Decimal):
        assert size > 0, 'invalid size'
        self.id = id
        self.price = price
        self.original_size = self.size = size
        self.side = side


class Trade(NamedTuple):
    takerid: OrderId
    makerid: OrderId
    size: Decimal
    price: Price


class Level:
    __slots__ = ('orders', 'volume')

    def __init__(self, orders=None):
        self.orders = orders or []
        self.volume = sum(o.size for o in self.orders)

    def append(self, o):
        self.orders.append(o)
        self.volume += o.size


class OrderBook:
    'sorted by price/time'
    __slots__ = ('bids', 'asks', 'on_event',
                 'levels', 'now')

    def __init__(self):
        self.bids = BitMap()
        self.asks = BitMap()
        self.levels = {}
        self.now = 0
        self.on_event = lambda name, evt: ...

    def limit_order(self, order: Order):
        assert order.size > 0, 'invalid order'
        self.now = time.time()
        order.order_time = self.now
        if order.side == Side.BUY:
            self.limit_order_buy(order)
        else:
            self.limit_order_sell(order)

    def limit_order_buy(self, order: Order):
        while self.asks:
            price = self.asks.min()
            if order.price < price:
                # 没有匹配的价格
                break

            lvl = self.levels[price]
            offset = 0
            for o in lvl.orders:
                size = min(order.size, o.size)
                order.size -= size
                o.size -= size
                lvl.volume -= size

                self.on_event('trade', Trade(order.id, o.id, size, o.price))

                if o.size == 0:
                    offset += 1

                if order.size == 0:
                    break

            if offset:
                lvl.orders = lvl.orders[offset:]

            if lvl.volume == 0:
                self.asks.discard(price)
                del self.levels[price]

            if order.size == 0:
                break

        if order.size > 0:
            if order.price in self.bids:
                self.levels[order.price].append(order)
            else:
                self.bids.add(order.price)
                self.levels[order.price] = Level([order])
            self.on_event('new', order)

    def limit_order_sell(self, order: Order):
        while self.bids:
            price = self.bids.max()
            if order.price > price:
                # 没有匹配的价格
                break

            lvl = self.levels[price]
            offset = 0
            for o in lvl.orders:
                size = min(order.size, o.size)
                order.size -= size
                o.size -= size
                lvl.volume -= size

                self.on_event('trade', Trade(order.id, o.id, size, o.price))

                if o.size == 0:
                    offset += 1

                if order.size == 0:
                    break

            if offset:
                lvl.orders = lvl.orders[offset:]

            if lvl.volume == 0:
                self.bids.discard(price)
                del self.levels[price]

            if order.size == 0:
                break

        if order.size > 0:
            if order.price in self.asks:
                self.levels[order.price].append(order)
            else:
                self.asks.add(order.price)
                self.levels[order.price] = Level([order])
            self.on_event('new', order)

    def cancel_order(self, price, orderid):
        lvl = self.levels[price]
        for o in lvl.orders:
            if o.id == orderid:
                lvl.orders.remove(o)
                lvl.volume -= o.size
                if lvl.volume == 0:
                    del self.levels[price]
                    (self.bids if o.side == Side.BUY else self.asks).discard(price)
                self.on_event('cancel', o)
                return o
