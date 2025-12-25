import smartpy as sp


@sp.module
def main():
    class A(sp.Contract):
        @sp.entrypoint
        def f(self, x):
            sp.trace(x * 2)
            sp.trace("double")


@sp.add_test()
def test():
    scenario = sp.test_scenario("Trace")
    c1 = main.A()
    scenario += c1
    c1.f(12)
