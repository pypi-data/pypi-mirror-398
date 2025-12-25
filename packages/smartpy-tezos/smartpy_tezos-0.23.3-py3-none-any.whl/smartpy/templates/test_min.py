import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        def __init__(self):
            self.data.r = 0

        @sp.entrypoint
        def ep1(self):
            a = 1
            b = 2
            self.data.r = sp.min(a, b)

        @sp.entrypoint
        def ep2(self):
            a = 3
            b = 4
            self.data.r = sp.max(a, b)

        @sp.entrypoint
        def ep1b(self, params):
            a = params
            b = 2
            self.data.r = sp.min(a, b)

        @sp.entrypoint
        def ep2b(self, params):
            a = params
            b = 4
            self.data.r = sp.max(a, b)


@sp.add_test()
def test():
    scenario = sp.test_scenario("Min")
    scenario.h1("Min / Max")
    c = main.C()
    scenario += c
    c.ep1()
    scenario.verify(c.data.r == 1)
    c.ep2()
    scenario.verify(c.data.r == 4)
    c.ep1b(1)
    scenario.verify(c.data.r == 1)
    c.ep2b(3)
    scenario.verify(c.data.r == 4)
