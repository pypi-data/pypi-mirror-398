# Fifo - Example for illustrative purposes only.

import smartpy as sp


@sp.module
def main():
    # The Fifo class defines a simple contract that handles push and pop instructions
    # on a first-in first-out basis.

    class SimpleFifo(sp.Contract):
        def __init__(self):
            self.data.first = 0
            self.data.last = -1
            self.data.saved = sp.cast({}, sp.map[sp.int, sp.int])

        @sp.entrypoint
        def pop(self):
            assert self.data.first < self.data.last
            del self.data.saved[self.data.first]
            self.data.first += 1

        @sp.entrypoint
        def push(self, element):
            self.data.last += 1
            self.data.saved[self.data.last] = element

        @sp.onchain_view
        def head(self):
            return self.data.saved[self.data.first]


if "main" in __name__:

    @sp.add_test()
    def test():
        scenario = sp.test_scenario("Fifo")
        scenario.h1("Simple Fifo Contract")
        c1 = main.SimpleFifo()
        scenario += c1
        c1.push(4)
        c1.push(5)
        c1.push(6)
        c1.push(7)
        c1.pop()
        # FIXME scenario.verify(sp.View(c1, "head")() == 5)
