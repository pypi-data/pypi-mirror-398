import smartpy as sp


@sp.module
def main():
    class MyContract(sp.Contract):
        def __init__(self):
            self.data.x = sp.cast(
                sp.record(a=1, b=2), sp.record(a=sp.int, b=sp.int).layout(("a", "b"))
            )
            self.data.y = sp.cast(
                sp.variant.A(42), sp.variant(A=sp.int, B=sp.int).layout(("A", "B"))
            )

        @sp.entrypoint
        def test_record(self):
            x = sp.cast(
                sp.record(c=3, d=4), sp.record(c=sp.int, d=sp.int).layout(("c", "d"))
            )
            self.data.x = sp.convert(x)
            assert self.data.x == sp.record(a=3, b=4)

        @sp.entrypoint
        def test_pair(self):
            self.data.x = sp.convert((5, 6))
            assert self.data.x == sp.record(a=5, b=6)

        @sp.entrypoint
        def test_variant(self):
            y = sp.cast(
                sp.variant.C(43), sp.variant(C=sp.int, D=sp.int).layout(("C", "D"))
            )
            self.data.y = sp.convert(y)
            assert self.data.y == sp.variant.A(43)


@sp.add_test()
def test():
    scenario = sp.test_scenario("Test_Convert")

    c = main.MyContract()
    scenario += c

    c.test_record()
    c.test_pair()
    c.test_variant()
