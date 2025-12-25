import smartpy as sp
from smartpy.templates import fa1_2, test_imported, welcome


@sp.add_test()
def test():
    scenario = sp.test_scenario("ImportWelcome", [welcome.main, test_imported.m2])
    scenario.h1("Welcome")
    c1 = welcome.main.MyContract(1, 1)
    scenario += c1
    scenario.add_module(fa1_2.m)
    c2 = fa1_2.m.Fa1_2TestFull(
        administrator=sp.test_account("Administrator").address,
        metadata=sp.big_map(),
        token_metadata={},
        ledger={},
    )
    scenario += c2
    scenario += test_imported.m2.MyContract()
    assert "main" in __name__
