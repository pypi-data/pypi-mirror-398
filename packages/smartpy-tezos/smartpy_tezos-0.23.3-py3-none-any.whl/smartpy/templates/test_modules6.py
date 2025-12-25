import smartpy as sp


@sp.module
def M1():
    # new way of importing
    import smartpy.stdlib.utils as utils

    m1 = {"a": 42}
    m2 = sp.cast({"a": 42}, sp.map[sp.string, sp.int])
    bm1 = sp.big_map({"a": 42})
    bm2 = sp.cast(sp.big_map({"a": 42}), sp.big_map[sp.string, sp.int])
    bm3 = sp.cast(sp.big_map(), sp.big_map[sp.string, sp.int])
    bm4 = sp.cast(sp.big_map({}), sp.big_map[sp.string, sp.int])

    class C(sp.Contract):
        def __init__(self):
            self.data.a = 0
            self.data.x = 0
            self.private.c = 42

        @sp.private(with_storage="read-write")
        def f(self, x):
            assert utils.nat_to_tez(0) == sp.tez(0)
            self.data.a = 1000
            return x + 2

        @sp.onchain_view
        def view_on(self, x):
            _ = self.private.c
            return x + 1

        @sp.offchain_view
        def view_off(self, x):
            return x + 1

        @sp.entrypoint
        def ep(self):
            assert self.f(2) == 4


@sp.add_test()
def test_new_imports1():
    # Recommended way
    # utils is imported within M1
    s = sp.test_scenario("Test new imports1", M1)
    c = M1.C()
    s += c
    c.ep()
    s.verify(c.view_off(1) == 2)

    # utils has to be accessed explicitly to be used outside of M1
    u = s.add_module("smartpy/stdlib/utils.spy")
    s.verify(u.mutez_to_nat(sp.mutez(1)) == sp.nat(1))


@sp.add_test()
def test_new_imports2():
    # utils is imported within M1 but can add after creating the scenario
    s = sp.test_scenario("Test new imports2")
    # does need to be added before contract origination though
    s.add_module(M1)
    c = M1.C()
    s += c
    c.ep()
    s.verify(c.view_off(1) == 2)

    # utils has to be accessed explicitly to be used outside of M1
    u = s.add_module("smartpy/stdlib/utils.spy")
    s.verify(u.mutez_to_nat(sp.mutez(1)) == sp.nat(1))


@sp.add_test()
def test_new_imports3():
    # utils is imported within M1 but can add after creating the scenario
    s = sp.test_scenario("Test new imports3")
    # does need to be added before contract origination though
    s.add_module(M1)
    c = M1.C()
    s += c
    c.ep()
    s.verify(c.view_off(1) == 2)

    # utils has to be accessed explicitly to be used outside of M1,
    # best not to mix old and new styles though
    s.verify(sp.utils.mutez_to_nat(sp.mutez(1)) == sp.nat(1))
    s.verify(sp.stdlib.utils.mutez_to_nat(sp.mutez(1)) == sp.nat(1))


# this doesnt work
# @sp.add_test()
# def test2():
#     s = sp.test_scenario("Test2", M1)
#     c = M1.C()
#     s += c
#     c.ep()
#     s.verify(c.view_off(1) == 2)
#     try:
#         s.verify(M1.utils.mutez_to_nat(sp.mutez(1)) == sp.nat(1))
#     except TypeError:
#         pass
#     else:
#         assert False


# shadow a previously defined module and re-add should error
oldM1 = M1


@sp.module
def M1():
    class C(sp.Contract):
        pass


@sp.add_test()
def test_old_imports5():
    s = sp.test_scenario("Test old imports5", M1)
    try:
        s.add_module(oldM1)
    except sp.TypeError_ as e:
        print(e)
    else:
        assert False


@sp.module
def M2():
    class C(sp.Contract):
        pass


@sp.module
def M3():
    import M2 as M

    class D(M.C):
        pass


@sp.add_test()
def test_inline_imports():
    s = sp.test_scenario("Test old imports5", M3)
    c = M3.D()
    s += c
