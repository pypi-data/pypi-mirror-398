# Store Value - Example for illustrative purposes only.

import smartpy as sp


@sp.module
def main():
    class Onchain_views(sp.Contract):
        def __init__(self):
            self.data.storedValue = 0

        @sp.onchain_view()
        def get_value(self):
            return self.data.storedValue

    class StoreValue(Onchain_views):
        def __init__(self, value):
            Onchain_views.__init__(self)
            self.data.storedValue = value

        @sp.entrypoint
        def replace(self, params):
            self.data.storedValue = params.value

    class StoreValue2(Onchain_views):
        def __init__(self, value):
            # self.verbose = True
            Onchain_views.__init__(self)
            self.data.storedValue = value

        @sp.entrypoint
        def add(self, params):
            self.data.storedValue += params.value

    class StoreValue3(StoreValue2):
        def __init__(self, value):
            StoreValue2.__init__(self, value)

        @sp.onchain_view()
        def new_name(self):
            return self.data.storedValue


if "main" in __name__:

    @sp.add_test()
    def test():
        sc = sp.test_scenario("StoreValue")
        c1 = main.StoreValue(12)
        sc += c1
        c2 = main.StoreValue2(14)
        sc += c2
        c3 = main.StoreValue3(14)
        sc += c3
        sc.verify(sp.View(c2, "get_value")() == 14)
        sc.verify(sp.View(c1, "get_value")() == 12)
        sc.verify(sp.View(c3, "get_value")() == 14)
