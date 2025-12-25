import sys

import smartpy as sp


@sp.module
def main():
    class MyContract(sp.Contract):
        def __init__(self):
            self.data.x = []


@sp.add_test()
def test():
    scenario = sp.test_scenario("Test")
    try:
        scenario += main.MyContract()
    except Exception as e:
        if scenario.simulation_mode() is sp.SimulationMode.MOCKUP:
            assert "Unknown primitive missing_type_conversion" in str(e)
            print(e, file=sys.stderr)
        else:
            raise e
