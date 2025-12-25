import smartpy as sp


@sp.module
def M():
    import smartpy.stdlib.fixed_point as fp

    class C(sp.Contract):
        def __init__(self):
            pass

        @sp.private
        def test_fixed_point(self):
            assert fp.mk((123, 2)) == sp.record(value=sp.int(123), exponent=2)

        @sp.private
        def test_add(self):
            v1 = fp.mk((123, 2))
            v2 = fp.mk((245, 2))
            assert fp.add((v1, v2)) == sp.record(value=sp.int(368), exponent=2)

        @sp.private
        def test_sub(self):
            v1 = fp.mk((245, 2))
            v2 = fp.mk((123, 2))
            assert fp.sub((v1, v2)) == sp.record(value=sp.int(122), exponent=2)

        @sp.private
        def test_mul(self):
            v1 = fp.mk((123, 3))
            v2 = fp.mk((25, 1))
            assert fp.mul((v1, v2)) == sp.record(value=sp.int(3075), exponent=4)

        @sp.private
        def test_eq(self):
            v1 = fp.mk((123, 3))
            v2 = fp.mk((25, 3))
            v3 = fp.mk((25, 3))
            assert not fp.eq((v1, v2))
            assert fp.eq((v2, v3))

        @sp.private
        def test_lt(self):
            v1 = fp.mk((123, 3))
            v2 = fp.mk((25, 3))
            v3 = fp.mk((25, 3))
            assert not fp.lt((v1, v2))
            assert not fp.lt((v2, v3))
            assert fp.lt((v2, v1))
            assert fp.lt((v3, v1))

        @sp.private
        def test_gt(self):
            v1 = fp.mk((123, 3))
            v2 = fp.mk((25, 3))
            v3 = fp.mk((25, 3))
            assert fp.gt((v1, v2))
            assert not fp.gt((v2, v3))
            assert not fp.gt((v2, v1))
            assert not fp.gt((v3, v1))

        @sp.entrypoint
        def ep(self):
            self.test_fixed_point()
            self.test_add()
            self.test_sub()
            self.test_mul()
            self.test_eq()
            self.test_lt()
            self.test_gt()


@sp.add_test()
def test():
    s = sp.test_scenario("Test")
    c = M.C()
    s += c
    c.ep()
