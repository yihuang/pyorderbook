# cython: language_level=3, boundscheck=False
cimport cython
import time
from enum import IntEnum
from typing import NamedTuple
from pyroaring import BitMap

from decimal import Decimal


OrderId = int
Price = int


cpdef enum:
    BUY = 0
    SELL = 1


@cython.freelist(100000)
cdef class Order:
    cdef public int id
    cdef public int price
    cdef public int original_size
    cdef public int size
    cdef public int side
    cdef public int order_time

    def __init__(self, int id, int side, int price, int size):
        assert size > 0, 'invalid size'
        self.id = id
        self.price = price
        self.original_size = self.size = size
        self.side = side


@cython.freelist(100000)
cdef class Level:
    cdef public list orders
    cdef public int volume

    def __init__(self, Order o):
        self.orders = [o]
        self.volume = o.size

    def append(self, Order o):
        self.orders.append(o)
        self.volume += o.size


cdef class OrderBook:
    'sorted by price/time'
    cdef public object bids
    cdef public object asks
    cdef public object on_event
    cdef public dict levels
    cdef public int now

    def __init__(self):
        self.bids = BitMap()
        self.asks = BitMap()
        self.levels = {}
        self.now = 0
        self.on_event = lambda name, evt: ...

    def limit_order(self, Order order):
        assert order.size > 0, 'invalid order'
        self.now = time.time()
        order.order_time = self.now
        if order.side == BUY:
            self.limit_order_buy(order)
        else:
            self.limit_order_sell(order)

    def limit_order_buy(self, Order order):
        cdef Level lvl
        cdef Order o
        cdef int size, price, offset
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

                self.on_event('trade', (order.id, o.id, size, o.price))

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
                self.levels[order.price] = Level(order)
            self.on_event('new', order)

    def limit_order_sell(self, Order order):
        cdef Level lvl
        cdef Order o
        cdef int size, price, offset
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

                self.on_event('trade', (order.id, o.id, size, o.price))

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
                self.levels[order.price] = Level(order)
            self.on_event('new', order)

    def cancel_order(self, int price, int orderid):
        cdef Level lvl
        cdef Order o
        lvl = self.levels[price]
        for o in lvl.orders:
            if o.id == orderid:
                lvl.orders.remove(o)
                lvl.volume -= o.size
                if lvl.volume == 0:
                    del self.levels[price]
                    (self.bids if o.side == BUY else self.asks).discard(price)
                self.on_event('cancel', o)
                return o
