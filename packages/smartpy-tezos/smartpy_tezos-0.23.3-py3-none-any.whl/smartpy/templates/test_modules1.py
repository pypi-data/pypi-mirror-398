import smartpy as sp


@sp.module
def M2():
    @sp.effects(with_storage="read-write")
    def f(x):
        self.data.x = 100
        if True:
            return x + 1
        else:
            return 2

    def g(x):
        return x

    f2 = sp.cast(
        f, sp.lambda_(int, int, with_storage="read-write", with_operations=False)
    )

    class C1(sp.Contract):
        def __init__(self):
            self.data.x = f(42)
            self.data.y = 100

        @sp.entrypoint
        def myEntryPoint(self, params):
            assert params == "abc"

    class C2(sp.Contract):
        def __init__(self, x):
            self.data.x = 42
            self.data.y = 100
            _ = f(
                42
            )  # f is inlined and can thus be used with different storage type each time
            x.f(42)  # x.f is unknown and thus defaults to no effects
            self.private.policy = sp.record(name="owner")

        @sp.entrypoint
        def ep(self, params):
            @sp.effects(with_storage="read-write")
            def h(x):
                pass

            assert params == f(params)


@sp.add_test()
def test():
    s = sp.test_scenario("Test")
    c1 = M2.C1()
    s += c1
    c2 = M2.C1()
    s += c2
    s.verify(c1.data.x == 43)
