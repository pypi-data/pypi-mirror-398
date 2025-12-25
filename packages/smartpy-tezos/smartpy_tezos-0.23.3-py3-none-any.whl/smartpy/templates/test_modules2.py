import smartpy as sp


@sp.module
def M2():
    class C(sp.Contract):
        def __init__(self, x: sp.int, y: sp.int):
            self.data.a = 42
            self.data.b = x + y
            self.data.x = 0

        @sp.entrypoint
        def myEntryPoint(self, params):
            assert params == "abc"
            self.data.x = 44


@sp.add_test()
def test():
    s = sp.test_scenario("Abbrevs")
    c = M2.C(x=43, y=0)
    s += c
    s.verify(c.data.a == 42)
    s.verify(c.data.b == 43)
    s.verify(c.data.x == 0)
    c.myEntryPoint("abc")
    s.verify(c.data.a == 42)
    s.verify(c.data.b == 43)
    s.verify(c.data.x == 44)
