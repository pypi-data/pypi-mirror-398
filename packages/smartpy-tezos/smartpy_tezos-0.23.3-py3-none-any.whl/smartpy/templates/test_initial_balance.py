import smartpy as sp


@sp.module
def main():
    class InitialBalance(sp.Contract):
        def __init__(self):
            self.data.x = 2

        @sp.private(with_storage="read-write")
        def sub(self, params):
            self.data.x = 3


@sp.add_test()
def test():
    scenario = sp.test_scenario("Sub")

    initialBalance = sp.mutez(123)

    c1 = main.InitialBalance()
    c1.set_initial_balance(initialBalance)
    scenario += c1
    scenario.verify(c1.balance == initialBalance)

    c2 = main.InitialBalance()
    c2.set_initial_balance(initialBalance)
    c2.set_initial_balance(initialBalance - sp.mutez(1))
    c2.set_initial_balance(initialBalance)
    scenario += c2
    scenario.verify(c2.balance == initialBalance)

    try:
        c2.set_initial_balance(initialBalance)
    except:
        pass
    else:
        # Don't raise error if the scenario failed earlier.
        # Needed for mockup.
        if not scenario.failed:
            raise AssertionError("set_initial_balance should fail after origination")
