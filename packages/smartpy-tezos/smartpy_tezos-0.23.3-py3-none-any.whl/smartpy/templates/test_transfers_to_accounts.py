import smartpy as sp


@sp.module
def main():
    class TestContract(sp.Contract):
        @sp.entrypoint
        def deposit(self):
            pass

        @sp.entrypoint
        def withdraw(self, address, quantity):
            sp.send(address, quantity)

        @sp.entrypoint
        def withdraw_all(self, address):
            sp.send(address, sp.balance)


@sp.add_test()
def test():
    sc = sp.test_scenario("Test")
    account = sp.test_account("test")
    c = main.TestContract()
    c.set_initial_balance(sp.mutez(100))
    sc += c
    c.deposit(_amount=sp.mutez(1000))
    sc.verify(c.balance == sp.mutez(1100))
    c.withdraw(address=account.address, quantity=sp.mutez(200))
    c.withdraw(
        address=account.address,
        quantity=sp.mutez(2000),
        _valid=False,
        _exception="Negative balance for KT1TezoooozzSmartPyzzSTATiCzzzwwBFA1",
    )
    sc.verify(c.balance == sp.mutez(900))
    c.withdraw_all(account.address)
    sc.verify(c.balance == sp.mutez(0))
