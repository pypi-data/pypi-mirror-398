import smartpy as sp


@sp.module
def main():
    class TestIsImplicitAccount(sp.Contract):
        @sp.entrypoint
        def ep(self, address, pkh):
            x = sp.is_implicit_account(address)
            assert (
                x.unwrap_some(error="not implicit account") == pkh
            ), "wrong implicit account"


@sp.add_test()
def test():
    scenario = sp.test_scenario("TestIsImplicitAccount")
    c1 = main.TestIsImplicitAccount()

    scenario += c1

    alice = sp.test_account("alice")
    c1.ep(address=alice.address, pkh=alice.public_key_hash)
    c1.ep(
        address=sp.address("KT1TezoooozzSmartPyzzSTATiCzzzwwBFA1"),
        pkh=sp.key_hash("WRONG"),
        _valid=False,
        _exception="not implicit account",
    )
