import smartpy as sp


@sp.module
def main():
    class Voting_Power(sp.Contract):
        def __init__(self, a, b):
            self.data.a = a
            self.data.b = b

        @sp.entrypoint
        def validate(self, key):
            self.data.a = sp.voting_power(sp.hash_key(key))
            self.data.b = sp.total_voting_power


@sp.add_test()
def test():
    scenario = sp.test_scenario("Voting_Power")
    scenario.h1("Voting Power")

    account = sp.test_account("tz1")

    c1 = main.Voting_Power(a=0, b=0)
    scenario += c1

    c1.validate(
        account.public_key,
        _voting_powers={account.public_key_hash: 1, sp.key_hash("tz2"): 4},
    )
