Proof-of-Concept implementation of matching engine in python.

Orderbook is implemented as a bitmap(pyroaring) of prices with related order list.

Performance is surprisingly not bad, benchmark shows 10k orders can be handled in 1ms on my laptop.
