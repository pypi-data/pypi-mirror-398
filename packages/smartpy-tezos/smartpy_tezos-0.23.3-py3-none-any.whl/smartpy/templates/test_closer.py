import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        @sp.entrypoint
        def test_none(self, p):
            assert p.is_none()

        @sp.entrypoint
        def test_some(self, p):
            assert p.is_some()


@sp.add_test()
def test():
    s = sp.test_scenario("Test")
    if s.simulation_mode() is sp.SimulationMode.MOCKUP:
        s.p("mockups need to know the type of ep params")
    else:
        s += main.C()
