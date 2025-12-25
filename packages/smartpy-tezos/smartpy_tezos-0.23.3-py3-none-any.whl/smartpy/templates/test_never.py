import smartpy as sp


@sp.module
def main():
    class MyContract(sp.Contract):
        def __init__(self, x):
            self.data.x = x

        @sp.entrypoint
        def entrypoint_1(self, params):
            match params:
                case A(a):
                    self.data.x = a + 12
                case B(b):
                    sp.never(b)

        @sp.entrypoint
        def entrypoint_1(self, params):
            sp.cast(params, sp.record(a=sp.int, b=sp.never))
            self.data.x = params.a


@sp.add_test()
def test():
    scenario = sp.test_scenario("Never")
    scenario.h1("Never")
    c1 = main.MyContract(x=0)
    scenario += c1
