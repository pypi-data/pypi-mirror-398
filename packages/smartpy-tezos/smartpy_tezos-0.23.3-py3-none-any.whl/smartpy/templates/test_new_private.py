import smartpy as sp


@sp.module
def M2():
    class C(sp.Contract):
        def __init__(self, x, y):
            self.data.s = 0
            self.private.x = x
            self.data.y = y

        @sp.entrypoint
        def myEntryPoint(self, params):
            if self.private.x:
                self.data.s += params
            else:
                assert False, "oops"


@sp.add_test()
def test():
    s = sp.test_scenario("Abbrevs")
    c = M2.C(x=True, y=0)
    s += c
