import smartpy as sp


@sp.module
def main():
    t: type = sp.record(address=sp.option[sp.int])

    class Test(sp.Contract):
        def __init__(self):
            self.data.address = None
            sp.cast(self.data, t)

        @sp.entrypoint
        def a(self, params):
            self.data = params

        @sp.entrypoint
        def b(self, params):
            self.data.address = params


@sp.add_test()
def test():
    scenario = sp.test_scenario("Tests")
    scenario += main.Test()
