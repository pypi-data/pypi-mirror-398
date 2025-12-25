# Shuffle - Example for illustrative purposes only

import smartpy as sp


@sp.module
def main():
    class Shuffle(sp.Contract):
        def __init__(self):
            self.data.a = sp.record(x1=-1, x2=-2)
            self.data.b = sp.record(x1=-3, x2=-4)

        @sp.entrypoint
        def swap(self):
            x = self.data.a.x1
            self.data.a.x1 = self.data.a.x2
            self.data.a.x2 = x

            self.data.b.x1 = self.data.b.x2
            # self.data.b.x1 += 1
            self.data.b.x2 *= 2


@sp.add_test()
def test():
    scenario = sp.test_scenario("Shuffle")
    scenario.h1("Shuffle")
    c = main.Shuffle()
    scenario += c
