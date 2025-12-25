import smartpy as sp


@sp.module
def main():
    class Called(sp.Contract):
        def __init__(self):
            self.data.calls = []

        @sp.entrypoint
        def call(self, v):
            sp.cast(v, sp.int)
            self.data.calls.push(v)

        @sp.entrypoint
        def reset(self):
            self.data.calls = []

    class MyContract(sp.Contract):
        def __init__(self):
            pass

        @sp.entrypoint
        def default(self):
            pass

        @sp.entrypoint
        def transfer(self, c):
            contract = sp.contract(sp.int, c, entrypoint="call")
            sp.transfer(1, sp.tez(0), contract.unwrap_some())
            sp.transfer(2, sp.tez(0), contract.unwrap_some())
            sp.transfer(3, sp.tez(0), contract.unwrap_some())

        @sp.entrypoint
        def transfer_operation(self, c):
            contract = sp.contract(sp.int, c, entrypoint="call")
            x = sp.transfer_operation(1, sp.tez(0), contract.unwrap_some())
            y = sp.transfer_operation(2, sp.tez(0), contract.unwrap_some())
            z = sp.transfer_operation(3, sp.tez(0), contract.unwrap_some())
            sp.operations.push(x)
            sp.operations.push(y)
            sp.operations.push(z)

        @sp.entrypoint
        def transfer_operation_list(self, c):
            contract = sp.contract(sp.int, c, entrypoint="call")
            operations = []
            x = sp.transfer_operation(1, sp.tez(0), contract.unwrap_some())
            y = sp.transfer_operation(2, sp.tez(0), contract.unwrap_some())
            z = sp.transfer_operation(3, sp.tez(0), contract.unwrap_some())
            operations.push(x)
            operations.push(y)
            operations.push(z)
            sp.operations = operations


if "main" in __name__:

    @sp.add_test()
    def test():
        sc = sp.test_scenario("Test operation order")
        c1 = main.MyContract()
        sc += c1
        c2 = main.Called()
        sc += c2

        sc.h2("Transfers")
        c1.transfer(c2.address)
        sc.verify_equal(c2.data.calls, [3, 2, 1])
        c2.reset()

        sc.h2("Transfers operations")
        c1.transfer_operation(c2.address)
        sc.verify_equal(c2.data.calls, [3, 2, 1])
        c2.reset()

        sc.h2("Transfers operations")
        c1.transfer_operation_list(c2.address)
        sc.verify_equal(c2.data.calls, [3, 2, 1])
        c2.reset()
