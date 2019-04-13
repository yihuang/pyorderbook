import time
from typing import Dict
from enum import IntEnum
from typing import NamedTuple
from collections import defaultdict

from dataclasses import dataclass
from sortedcontainers import SortedList
from decimal import Decimal


OrderId = int
Price = Decimal


class Side(IntEnum):
    BUY = 0
    SELL = 1


@dataclass
class Order:
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


def order_key(self):
    return (self.price, self.order_time)


def order_key_reversed(self):
    return (-self.price, self.order_time)


class Trade(NamedTuple):
    takerid: OrderId
    makerid: OrderId
    size: Decimal
    price: Price


@dataclass
class OrderBook:
    # sorted by price/time
    bids: SortedList
    asks: SortedList
    orders: Dict[OrderId, Order]
    depth: Dict[Price, int]
    now: float

    def __init__(self):
        self._next_order_id = 0
        self.bids = SortedList(key=order_key_reversed)  # from high to low
        self.asks = SortedList(key=order_key)  # from low to high
        self.orders = {}
        self.depth = defaultdict(int)
        self.now = 0

    def next_order_id(self):
        self._next_order_id = self._next_order_id + 1
        return self._next_order_id

    def on_event(self, evtname, evt):
        if evtname == 'trade':
            self.depth[evt.price] -= evt.size
        elif evtname == 'new':
            self.depth[evt.price] += evt.size
        elif evtname == 'cancel':
            self.depth[evt.price] -= evt.size

    def limit_order(self, order: Order):
        self.now = time.time()
        order.order_time = self.now
        order.id = self.next_order_id()
        if order.side == Side.BUY:
            self.limit_order_buy(order)
        else:
            self.limit_order_sell(order)

    def limit_order_buy(self, order: Order):
        offset = 0
        for o in self.asks:
            if order.price < o.price:
                # 没有匹配的价格
                break

            if order.size > o.size:  # o 完全成交
                self.on_event('trade', Trade(order.id, o.id, o.size, o.price))
                order.size -= o.size
                o.size = 0
                offset += 1
            else:  # order 完全成交
                self.on_event('trade', Trade(order.id, o.id, order.size, o.price))
                o.size -= order.size
                order.size = 0
                if o.size == 0:
                    offset += 1
                break

        for i in range(offset):
            self.asks.pop(0)

        if order.size > 0:
            self.bids.add(order)
            self.orders[order.id] = order
            self.on_event('new', order)

    def limit_order_sell(self, order: Order):
        offset = 0
        for o in self.bids:
            if order.price > o.price:
                # 没有匹配的价格
                break

            if order.size > o.size:  # o 完全成交
                self.on_event('trade', Trade(order.id, o.id, o.size, o.price))
                order.size -= o.size
                o.size = 0
                offset += 1
            else:  # order 完全成交
                self.on_event('trade', Trade(order.id, o.id, order.size, o.price))
                o.size -= order.size
                order.size = 0
                if o.size == 0:
                    offset += 1
                break

        for i in range(offset):
            self.bids.pop(0)

        if order.size > 0:
            self.asks.add(order)
            self.orders[order.id] = order
            self.on_event('new', order)

    def cancel_order(self, orderid):
        order = self.orders.pop(orderid)
        if order.side == Side.BUY:
            self.bids.remove(order)
        else:
            self.asks.remove(order)
        self.on_event('cancel', order)
