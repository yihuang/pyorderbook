Proof-of-Concept implementation of matching engine in python.

Orderbook is implemented as a bitmap(pyroaring) of prices with related orders.

Benchmark shows 1m orders can be handled in 4-5 seconds in my laptop.

After optimize with cython, 1m orders can be handled in 1.2 seconds.
