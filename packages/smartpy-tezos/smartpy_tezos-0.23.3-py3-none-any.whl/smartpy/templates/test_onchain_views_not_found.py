import smartpy as sp


@sp.module
def main():
    class Test(sp.Contract):
        def __init__(self):
            self.data.value = 0

        @sp.onchain_view()
        def other(self, x):
            return 1 + x


if "main" in __name__:

    @sp.add_test()
    def test2():
        scenario = sp.test_scenario("Test")
        scenario.add_module(main)
        if scenario.simulation_mode() is sp.SimulationMode.MOCKUP:
            scenario.p("mockups - TODO missing views")
        else:
            provider = sp.address("KT1")
            scenario.verify(sp.view("a_view", provider, 0, t=sp.nat) == None)

        c1 = main.Test()
        scenario += c1
        scenario.verify(c1.other(42) == 43)
        scenario.verify(sp.view("other", c1.address, 1, t=sp.int_or_nat) == sp.Some(2))
        scenario.verify(sp.view("other", c1.address, 1) == sp.Some(2))
        if scenario.simulation_mode() is sp.SimulationMode.MOCKUP:
            scenario.p("mockups - TODO missing views")
        else:
            scenario.verify(sp.view("missing_view", c1.address, 1) == None)
        scenario.verify(sp.view("other", c1.address, 1, t=sp.int) == sp.Some(2))
        scenario.verify(sp.view("other", c1.address, 1, t=sp.nat) == None)
