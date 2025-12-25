import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        def __init__(self):
            self.data.m = {"abc": sp.record(a=10, b=20)}
            self.data.out = "z"

        @sp.entrypoint
        def ep1(self, params):
            (x, y) = params
            assert x == "x"
            assert y == 2

        @sp.entrypoint
        def ep2(self, params):
            (x, y, z) = params
            assert x == "x"
            assert y == 2
            assert z

        @sp.entrypoint
        def ep3(self, params):
            sp.cast(params, sp.record(x=sp.string, y=int, z=bool))
            record(x=x, z=z).match = params
            assert x == "x"
            assert z

        @sp.entrypoint
        def ep4(self, params):
            sp.cast(params.x01, sp.int)
            sp.cast(params.x02, sp.key)
            sp.cast(params.x03, sp.string)
            sp.cast(params.x04, sp.timestamp)
            sp.cast(params.x05, sp.bytes)
            sp.cast(params.x06, sp.address)
            sp.cast(params.x07, sp.bool)
            sp.cast(params.x08, sp.key_hash)
            sp.cast(params.x09, sp.signature)
            sp.cast(params.x10, sp.mutez)
            record(x07, x03).match = params
            assert x03 == "x"
            assert x07

        @sp.entrypoint
        def ep5(self, params):
            (a, b, c, d) = params
            assert a * b + c * d == 12

        @sp.entrypoint
        def ep6(self, params):
            (a, b, c, d) = params
            sp.cast(c, int)
            assert a * b + d == 12

        @sp.entrypoint
        def ep7(self):
            k = "abc"
            with sp.modify_record(self.data.m[k]) as data:
                k = "xyz" + k
            self.data.out = k


@sp.add_test()
def test():
    s = sp.test_scenario("Match")
    c = main.C()
    s += c
    if s.simulation_mode() is sp.SimulationMode.MOCKUP:
        s.p("mockups - TODO tuples>2")
        return

    c.ep1(("x", 2))
    c.ep2(("x", 2, True))
    c.ep3(x="x", y=2, z=True)
    c.ep5((1, 6, 2, 3))
    c.ep6((1, 6, 2, 6))
    c.ep7()
