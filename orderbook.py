import time
from typing import Dict
from enum import IntEnum
from typing import NamedTuple
from pyroaring import BitMap

from dataclasses import dataclass
from decimal import Decimal


OrderId = int
Price = int


class Side(IntEnum):
    BUY = 0
    SELL = 1


@dataclass
class Order:
    __slots__ = ('id', 'price', 'original_size', 'size', 'side', 'order_time')
    id: OrderId
    price: Price
    original_size: Decimal
    size: Decimal
    side: Side
    order_time: float  # 进入orderbook时间

    def __init__(self, side, price, size):
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


@dataclass
class OrderBook:
    'sorted by price/time'
    bids: BitMap
    asks: BitMap
    levels: Dict[int, Level]
    orders: Dict[OrderId, Order]
    now: float

    def __init__(self):
        self._next_order_id = 0
        self.bids = BitMap()
        self.asks = BitMap()
        self.levels = {}
        self.orders = {}
        self.now = 0

    def next_order_id(self):
        self._next_order_id = self._next_order_id + 1
        return self._next_order_id

    def on_event(self, evtname, evt):
        pass

    def limit_order(self, order: Order):
        if order.size == 0:
            return
        # self.now = time.time()
        # order.order_time = self.now
        order.id = self.next_order_id()
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

            if not lvl.volume:
                self.asks.remove(price)
                del self.levels[price]

            if order.size == 0:
                break

        if order.size > 0:
            if order.price in self.bids:
                self.levels[order.price].append(order)
            else:
                self.bids.add(order.price)
                self.levels[order.price] = Level([order])
            self.orders[order.id] = order
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

            if not lvl.volume:
                self.bids.remove(price)
                del self.levels[price]

            if order.size == 0:
                break

        if order.size > 0:
            if order.price in self.asks:
                self.levels[order.price].append(order)
            else:
                self.asks.add(order.price)
                self.levels[order.price] = Level([order])
            self.orders[order.id] = order
            self.on_event('new', order)

    def cancel_order(self, orderid):
        order = self.orders.pop(orderid)
        if order.side == Side.BUY:
            self.bids.remove(order.price)
        else:
            self.asks.remove(order.price)
        self.levels[order.price].orders.remove(order)
        self.levels[order.price].volume -= order.size
        self.on_event('cancel', order)
