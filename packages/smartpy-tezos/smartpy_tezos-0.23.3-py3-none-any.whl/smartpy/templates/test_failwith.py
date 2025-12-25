import smartpy as sp


@sp.module
def main():
    class C1(sp.Contract):
        def __init__(self):
            self.data.f = None

        @sp.entrypoint
        def ep(self):
            def f(x):
                if x == 0:
                    raise "zero"
                else:
                    return 1

            self.data.f = sp.Some(f)

    class C2(sp.Contract):
        @sp.entrypoint
        def ep(self, params):
            if params == 0:
                raise "zero"
            else:
                raise "non-zero"

    class C3(sp.Contract):
        def __init__(self):
            self.data.x = 1

        @sp.entrypoint
        def ep1(self):
            raise "A"
            raise "B"

        @sp.entrypoint
        def ep2(self):
            raise "A"
            self.data.x = 2

    class C4(sp.Contract):
        @sp.entrypoint
        def ep1(self):
            assert 1 == 2

        @sp.entrypoint
        def ep2(self):
            assert 1 == 2


@sp.add_test()
def test():
    scenario = sp.test_scenario("Test")
    scenario += main.C1()
    scenario += main.C2()
    scenario += main.C3()
    scenario += main.C4()
