import smartpy as sp


@sp.module
def main():
    class Test(sp.Contract):
        def __init__(self):
            self.data.value = sp.int(0)

        @sp.onchain_view()
        def other(self, x):
            sp.cast(x, int)
            assert x < self.data.value
            return x * x

        @sp.onchain_view()
        def square_exn(self, x):
            sp.cast(x, int)
            raise x * x
            return x


if "main" in __name__:

    @sp.add_test()
    def test():
        scenario = sp.test_scenario("Test")
        c = main.Test()
        scenario += c
        scenario.compute(c.other(-5))
        if scenario.simulation_mode() is sp.SimulationMode.MOCKUP:
            scenario.p(
                "mockup mode doesnt support sp.is_failing and sp.catch_exception"
            )
            return

        scenario.verify(sp.is_failing(c.other(5)))
        scenario.verify(~sp.is_failing(c.other(-5)))
        scenario.verify(
            sp.catch_exception(c.other(5))
            == sp.Some("Assert failure: params < self.data.value")
        )
        scenario.verify(
            sp.catch_exception(c.other(5), t=sp.string)
            == sp.Some("Assert failure: params < self.data.value")
        )
        scenario.verify(sp.catch_exception(c.other(-5), t=sp.string) == None)
        scenario.verify(sp.catch_exception(c.other(-5), t=sp.int) == None)
        scenario.verify(sp.catch_exception(c.square_exn(-5), t=sp.int) == sp.Some(25))
