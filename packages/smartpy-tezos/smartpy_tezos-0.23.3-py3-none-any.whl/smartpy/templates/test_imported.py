import smartpy as sp


@sp.module
def m2():
    class MyContract(sp.Contract):
        def __init__(self):
            self.data.x = 0

        @sp.entrypoint
        def entrypoint_1(self, params):
            (a, b) = params
            (c, d) = b
            self.data.x += a * c * d


@sp.add_test()
def test():
    scenario = sp.test_scenario("Minimal")
    scenario.h1("Minimal")
    c1 = m2.MyContract()
    scenario += c1
