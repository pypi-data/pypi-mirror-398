import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        @sp.entrypoint
        def ep(self):
            x = sp.record(a=sp.nat(1), b=sp.nat(2))
            x.a = 15

        @sp.entrypoint
        def ep2(self, params):
            sp.cast(params, sp.pair[int, int])


@sp.add_test()
def test():
    scenario = sp.test_scenario("LocalRecord")
    scenario.h1("Local record")
    scenario += main.C()
