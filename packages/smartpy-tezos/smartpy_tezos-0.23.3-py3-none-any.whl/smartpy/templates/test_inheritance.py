import smartpy as sp

# Various techniques to edit entrypoints


@sp.module
def main():
    class MyContract(sp.Contract):
        def __init__(self, x, y):
            self.data.x = x
            self.data.y = y
            self.data.t = sp.Some(0)

        @sp.entrypoint
        def myEntryPoint(self, params):
            assert self.data.x <= 100
            self.data.x += params

        @sp.entrypoint
        def myEntryPointOther(self):
            self.data.x += 10

        @sp.entrypoint
        def myEntryPointXXX(self, params):
            assert self.data.x <= 1000
            self.data.x += params

        @sp.private(with_storage="read-write")
        def some_helper(self, params):
            sp.cast(params, sp.nat)
            pass

    class MyContract2(MyContract):
        def __init__(self, x, y):
            MyContract.__init__(self, 1, 2)
            self.data.z = 42
            self.data.t = None

        # Replace an inherited entrypoint
        @sp.entrypoint
        def myEntryPoint(self, params):
            self.data.y = 12345
            self.some_helper(params + 2)

        # Replace an inherited private lambda
        @sp.private(with_storage="read-write")
        def some_helper(self, params):
            self.data.y += params

        # Add a new entrypoint
        @sp.entrypoint
        def myEntryPoint2(self):
            pass


# Tests
@sp.add_test()
def test():
    scenario = sp.test_scenario("Inheritance")
    c1 = main.MyContract2(12, 15)
    scenario += c1
