import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        def __init__(self):
            self.data.x = 0

        @sp.entrypoint
        def ep(self, x):
            self.data.x = x


if "templates" not in __name__:

    @sp.add_test()
    def test():
        sc = sp.test_scenario("Test")
        c1 = main.C()
        sc += c1

        if not sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            print("Code JSON")
            print(c1.origination_result["code_json"])
            print("\nCode TZ")
            print(c1.origination_result["code_tz"])
            print("\nStorage JSON")
            print(c1.origination_result["storage_json"])
            print("\nStorage TZ")
            print(c1.origination_result["storage_tz"])
            print("\nStorage PY")
            print(c1.origination_result["storage_py"])
            print("\nTypes PY")
            print(c1.origination_result["types_py"])

        c1.ep(42)
        if not sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            print("\nArg Michelson")
            print(sc.entrypoint_calls[-1][1]["message"]["arg_michelson"])
            print("\nArg Micheline")
            print(sc.entrypoint_calls[-1][1]["message"]["arg_micheline"])
