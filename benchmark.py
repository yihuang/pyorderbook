import random
from decimal import Decimal
import pickle
from orderbook import Order, Side, OrderBook


class TestOrderBook(OrderBook):
    def on_event(self, evtname, evt):
        print(evtname, evt.price, evt.size)


def gen_random_order():
    return Order(
        random.choice([Side.BUY, Side.SELL]),
        Decimal(random.randrange(50, 150)),
        Decimal(random.randrange(1000))
    )


def gen_tests(n):
    return [gen_random_order() for i in range(n)]


# tests = gen_tests(1000000)
# pickle.dump(tests, open('test.data', 'wb'))
tests = pickle.load(open('test.data', 'rb'))


def bench(n):
    book = OrderBook()
    length = len(tests)
    for i in range(n):
        book.limit_order(tests[i % length])


if __name__ == '__main__':
    import perf
    runner = perf.Runner()
    runner.timeit(
        name="orderbook",
        stmt="bench(10000)",
        setup="from __main__ import bench")
