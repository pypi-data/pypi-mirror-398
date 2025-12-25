import smartpy as sp


@sp.module
def M2():
    x = 42

    target = x

    def inc(y):
        return y + 1

    def f(y, z):
        return y + z

    class C(sp.Contract):
        @sp.entrypoint
        def ep(self, params):
            assert f(sp.record(y=1, z=2)) == 3
            assert params == inc(42)
            pass
            assert params == 43
            assert params == target + 1


@sp.add_test()
def test():
    s = sp.test_scenario("Test")
    c = M2.C()
    s += c
    c.ep(43)
