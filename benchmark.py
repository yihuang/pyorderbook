import os
import random
import pickle
from orderbook import Order, Side, OrderBook


class TestOrderBook(OrderBook):
    def on_event(self, evtname, evt):
        print(evtname, evt.price, evt.size)


def gen_random_order():
    return Order(
        random.choice([Side.BUY, Side.SELL]),
        random.randrange(50, 150),
        random.randrange(1000)
    )


def gen_tests(n):
    return [gen_random_order() for i in range(n)]


if not os.path.exists('test.data'):
    tests = gen_tests(1000000)
    pickle.dump(tests, open('test.data', 'wb'))
else:
    tests = pickle.load(open('test.data', 'rb'))


def bench(n):
    book = OrderBook()
    length = len(tests)
    for i in range(n):
        book.limit_order(tests[i % length])


if __name__ == '__main__':
    print('start')
    import timeit
    print(timeit.repeat('bench(10000)', 'from __main__ import bench', repeat=5, number=100))
