import smartpy as sp


@sp.module
def main():
    class C1(sp.Contract):
        pass

    class C2(sp.Contract):
        @sp.entrypoint
        def ep(self):
            pass


@sp.add_test()
def test():
    scenario = sp.test_scenario("Void")
    scenario.h1("Void / Unit")
    scenario += main.C1()
    scenario += main.C2()
