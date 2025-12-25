import smartpy as sp


@sp.module
def main():
    import smartpy.stdlib.utils as utils

    class TestAddressComparison(sp.Contract):
        @sp.entrypoint
        def test(self, x):
            assert utils.mutez_to_nat(sp.amount) == x
            assert utils.nat_to_mutez(x) == sp.amount

        @sp.entrypoint
        def test_diff(self, x, y):
            sp.cast(x, sp.mutez)
            sp.cast(y, sp.mutez)
            r = x - y

    class MyContract(sp.Contract):
        def __init__(self):
            self.data.result = None

        @sp.entrypoint
        def store(self, params):
            self.data.result = sp.Some(params)

        @sp.entrypoint
        def decrease(self, params):
            self.data.result = sp.Some(self.data.result.unwrap_some() - params)

        @sp.entrypoint
        def sub(self, params):
            self.data.result = sp.sub_mutez(params.x, params.y)


if "templates" not in __name__:

    @sp.add_test()
    def test():
        scenario = sp.test_scenario("Test")
        c1 = main.TestAddressComparison()

        scenario += c1

        c1.test(10, _amount=sp.mutez(10))
        c1.test(10000000, _amount=sp.tez(10))
        c1.test_diff(x=sp.mutez(100), y=sp.mutez(50))
        c1.test_diff(x=sp.mutez(70), y=sp.mutez(100), _valid=False)

    @sp.add_test()
    def test():
        scenario = sp.test_scenario("Test2")
        c1 = main.MyContract()
        scenario += c1
        c1.store(sp.mutez(42))
        c1.decrease(sp.mutez(22))
        c1.decrease(sp.mutez(22), _valid=False)
        c1.sub(sp.record(x=sp.mutez(1), y=sp.mutez(2)))
        scenario.verify(c1.data.result == None)
        c1.sub(sp.record(x=sp.mutez(100), y=sp.mutez(1)))
        scenario.verify(c1.data.result == sp.Some(sp.mutez(99)))
