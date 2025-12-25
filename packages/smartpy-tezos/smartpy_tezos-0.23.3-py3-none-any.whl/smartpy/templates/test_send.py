import smartpy as sp


@sp.module
def main():
    dest1 = sp.address("tz1M9CMEtsXm3QxA7FmMU2Qh7xzsuGXVbcDr")
    dest2 = sp.address("tz1YtuZ4vhzzn7ssCt93Put8U9UJDdvCXci4")

    class C1(sp.Contract):
        @sp.entrypoint
        def ep(self):
            sp.send(dest1, sp.tez(1))

    class C2(sp.Contract):
        @sp.entrypoint
        def ep(self, cond):
            if cond == True:
                sp.send(dest2, sp.tez(2))

    class C3(sp.Contract):
        @sp.entrypoint
        def ep1(self):
            sp.send(dest1, sp.tez(1))

        @sp.entrypoint
        def ep2(self):
            pass

    class C4(sp.Contract):
        @sp.entrypoint
        def ep1(self):
            sp.send(dest1, sp.tez(1))

        @sp.entrypoint
        def ep2(self, cond):
            if cond == True:
                sp.send(dest2, sp.tez(2))

    class C5(sp.Contract):
        @sp.entrypoint
        def ep(self, params):
            if params == True:
                sp.send(dest1, sp.tez(1))
            else:
                assert params == False

    class C6(sp.Contract):
        @sp.entrypoint
        def ep(self):
            c = sp.contract(sp.int, dest1, entrypoint="myEntryPoint")
            sp.transfer(-42, sp.mutez(0), c.unwrap_some())


@sp.add_test()
def test():
    scenario = sp.test_scenario("Send")
    scenario.h1("Send")
    scenario += main.C1()
    scenario += main.C2()
    scenario += main.C3()
    scenario += main.C4()
    scenario += main.C5()
    scenario += main.C6()
