import pyximport; pyximport.install()
import os
import random
import pickle
from orderbook import Order, BUY, SELL, OrderBook


class TestOrderBook(OrderBook):
    def on_event(self, evtname, evt):
        print(evtname, evt.price, evt.size)


def gen_random_order(i):
    return Order(
        i,
        random.choice([BUY, SELL]),
        random.randrange(50, 150),
        random.randrange(1, 1000)
    )


def gen_tests(n):
    return [gen_random_order(i) for i in range(n)]


if not os.path.exists('test.data'):
    tests = gen_tests(1000000)
    pickle.dump(tests, open('test.data', 'wb'))
else:
    tests = pickle.load(open('test.data', 'rb'))


def bench(n):
    book = OrderBook()
    length = len(tests)
    for i in range(n):
        o = tests[i % length]
        book.limit_order(Order(
            o.id, o.side, o.price, o.original_size
        ))


if __name__ == '__main__':
    print('start')
    import timeit
    print(timeit.repeat('bench(10000)', 'from __main__ import bench', repeat=5, number=100))
