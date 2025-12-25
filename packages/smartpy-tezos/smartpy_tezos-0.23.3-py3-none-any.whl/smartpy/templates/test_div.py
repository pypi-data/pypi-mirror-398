# Div - Example for illustrative purposes only.

import smartpy as sp


@sp.module
def main():
    class TestDiv(sp.Contract):
        def __init__(self):
            self.data.a = None
            self.data.b = None
            self.data.c = None
            self.data.d = None
            self.data.e = None
            self.data.f = None
            self.data.g = None
            self.data.h = None
            self.data.i = None
            self.data.j = None
            self.data.k = None
            self.data.l = None
            self.data.m = None

        @sp.entrypoint
        def test(self, params):
            self.data.a = sp.ediv(1, 0)
            self.data.b = sp.ediv(-1, 0)
            self.data.c = sp.ediv(1, 12)
            self.data.d = sp.ediv(-1, 12)
            self.data.e = sp.ediv(-1, -12)
            self.data.f = sp.ediv(15, 12)
            self.data.g = sp.ediv(-15, 12)
            self.data.h = sp.ediv(-15, -12)
            self.data.i = sp.ediv(sp.tez(2), sp.mutez(100))
            self.data.j = sp.ediv(sp.tez(2), sp.mutez(101))
            self.data.k = sp.ediv(sp.tez(2), sp.tez(100))
            self.data.l = sp.ediv(sp.tez(2), 15)
            self.data.m = sp.ediv(sp.amount, sp.cast(params, sp.nat))


@sp.add_test()
def test():
    scenario = sp.test_scenario("Div")
    c1 = main.TestDiv()
    scenario.h1("Division")
    scenario += c1
    c1.test(2000, _amount=sp.tez(2))
    scenario.show(c1.data)
    scenario.verify_equal(
        c1.data,
        sp.record(
            a=None,
            b=None,
            c=sp.Some((0, 1)),
            d=sp.Some((-1, 11)),
            e=sp.Some((1, 11)),
            f=sp.Some((1, 3)),
            g=sp.Some((-2, 9)),
            h=sp.Some((2, 9)),
            i=sp.Some((20000, sp.tez(0))),
            j=sp.Some((19801, sp.mutez(99))),
            k=sp.Some((0, sp.tez(2))),
            l=sp.Some((sp.mutez(133333), sp.mutez(5))),
            m=sp.Some((sp.mutez(1000), sp.tez(0))),
        ),
    )
