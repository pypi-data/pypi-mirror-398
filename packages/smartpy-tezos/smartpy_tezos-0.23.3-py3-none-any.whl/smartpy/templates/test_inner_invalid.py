# Inner operation is invalid, calling other contracts - Example for illustrative purposes only.

import smartpy as sp


@sp.module
def main():
    class Test(sp.Contract):
        def __init__(self):
            self.data.counter = 0

        @sp.entrypoint
        def run(self, n):
            assert self.data.counter * n != 9
            if n > 1:
                self.data.counter += 1
                sp.transfer(n - 1, sp.mutez(0), sp.self_entrypoint("run"))

        @sp.entrypoint
        def reset(self):
            self.data.counter = 0

        @sp.entrypoint
        def compute(self, n):
            sp.transfer(n, sp.mutez(0), sp.self_entrypoint("run"))


@sp.add_test()
def test():
    scenario = sp.test_scenario("Test")
    scenario.h1("Test template - Inter-Contract Calls")
    test = main.Test()
    scenario += test
    for i in range(0, 20):
        valid = i not in [6, 10]
        test.reset()
        test.compute(i, _valid=valid)
        scenario.verify(test.data.counter == (max(0, i - 1) if valid else 0))
