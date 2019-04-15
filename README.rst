Proof-of-Concept implementation of matching engine in python.

Orderbook is implemented as a bitmap(pyroaring) of prices with related orders.

Benchmark shows 10k orders can be handled in 4-5 seconds in my laptop.
