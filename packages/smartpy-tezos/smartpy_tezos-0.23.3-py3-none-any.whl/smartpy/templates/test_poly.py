import smartpy as sp


@sp.module
def main():
    class MyContract(sp.Contract):
        @sp.entrypoint
        def poly(self, params):
            pass


@sp.add_test()
def test():
    s = sp.test_scenario("test")
    c = main.MyContract()
    try:
        s += c
        c.poly("abc")
    except Exception as e:
        print(e)
        if s.simulation_mode() is sp.SimulationMode.MOCKUP:
            assert "Unknown primitive missing_type_conversion" in str(e)
