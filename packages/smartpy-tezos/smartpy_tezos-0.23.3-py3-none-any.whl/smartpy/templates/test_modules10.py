import smartpy as sp


@sp.module
def t():
    r: type = sp.record(a=sp.nat, b=sp.nat)


@sp.module
def main():
    import t

    class A(sp.Contract):
        def __init__(self, r: t.r):
            # sp.cast(r, t.r)
            self.data.r = r

        @sp.entrypoint
        def ep(self, r):
            self.data.r = r


@sp.add_test()
def test():
    s = sp.test_scenario("Test1")
    a1 = main.A(sp.record(a=1, b=2))
    s += a1


@sp.add_test()
def test():
    s = sp.test_scenario("Test2")
    s.add_module(main)
    a1 = main.A(sp.record(a=1, b=2))
    s += a1
