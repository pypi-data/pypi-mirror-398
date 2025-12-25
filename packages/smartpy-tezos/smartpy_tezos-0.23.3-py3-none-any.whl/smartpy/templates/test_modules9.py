import smartpy as sp


@sp.module
def main():
    class A(sp.Contract):
        def __init__(self, x):
            self.data.x = x
            self.private.a = 42
            self.private.b = 43

        @sp.entrypoint
        def ep(self, param):
            assert param == self.private.a


@sp.add_test()
def test():
    s = sp.test_scenario("Test")

    a1 = main.A(0)
    s += a1
    a1.ep(42)
    a1.ep(100, _valid=False)
    s.verify(a1.private.a == 42)
