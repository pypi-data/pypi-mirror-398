import smartpy as sp


@sp.module
def main():
    class MyContract(sp.Contract):
        @sp.entrypoint
        def bounce(self):
            sp.send(sp.source, sp.amount)

        @sp.entrypoint
        def bounce2(self):
            sp.send(sp.source, sp.tez(1))
            sp.send(sp.source, sp.amount - sp.tez(1))


@sp.add_test()
def test():
    scenario = sp.test_scenario("Test")
    scenario.h1("Send Back")
    scenario += main.MyContract()
