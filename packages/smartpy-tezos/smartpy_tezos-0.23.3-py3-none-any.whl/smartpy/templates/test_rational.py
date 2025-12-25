import smartpy as sp


@sp.module
def M():
    import smartpy.stdlib.rational as rational

    class C(sp.Contract):
        def __init__(self):
            pass

        @sp.private
        def test_rational(self):
            assert rational.mk((3, 5)) == sp.record(
                numerator=sp.int(3), denominator=sp.nat(5)
            )
            assert rational.mk((-3, -5)) == sp.record(
                numerator=sp.int(3), denominator=sp.nat(5)
            )
            assert rational.mk((3, -5)) == sp.record(
                numerator=sp.int(-3), denominator=sp.nat(5)
            )

        @sp.private
        def test_ceil(self):
            r1 = rational.mk((4, 3))
            r2 = rational.mk((4, 2))
            r3 = rational.mk((4, 1))
            assert rational.ceil(r1) == sp.int(2)
            assert rational.ceil(r2) == sp.int(2)
            assert rational.ceil(r3) == sp.int(4)

        @sp.private
        def test_floor(self):
            r1 = rational.mk((3, 1))
            r2 = rational.mk((2, 3))
            r3 = rational.mk((7, 2))
            assert rational.floor(r1) == sp.int(3)
            assert rational.floor(r2) == sp.int(0)
            assert rational.floor(r3) == sp.int(3)

        @sp.private
        def test_round(self):
            r1 = rational.mk((1, 3))
            r2 = rational.mk((2, 3))
            r3 = rational.mk((3, 3))
            r4 = rational.mk((4, 3))
            r5 = rational.mk((5, 3))
            r6 = rational.mk((6, 3))
            r7 = rational.mk((7, 3))
            r8 = rational.mk((8, 3))
            r9 = rational.mk((9, 3))
            r10 = rational.mk((10, 3))
            r11 = rational.mk((11, 3))
            r12 = rational.mk((12, 3))
            assert rational.round(r1) == sp.int(0)
            assert rational.round(r2) == sp.int(1)
            assert rational.round(r3) == sp.int(1)
            assert rational.round(r4) == sp.int(1)
            assert rational.round(r5) == sp.int(2)
            assert rational.round(r6) == sp.int(2)
            assert rational.round(r7) == sp.int(2)
            assert rational.round(r8) == sp.int(3)
            assert rational.round(r9) == sp.int(3)
            assert rational.round(r10) == sp.int(3)
            assert rational.round(r11) == sp.int(4)
            assert rational.round(r12) == sp.int(4)

        @sp.private
        def test_rational_add(self):
            r1 = rational.mk((3, 5))
            r2 = rational.mk((4, 3))
            res = rational.add((r1, r2))
            assert res.numerator == sp.int(29)
            assert res.denominator == sp.nat(15)

        @sp.private
        def test_rational_sub(self):
            r1 = rational.mk((1, 5))
            r2 = rational.mk((5, 3))
            res = rational.sub((r1, r2))
            assert res.numerator == sp.int(-22)
            assert res.denominator == sp.nat(15)
            r1 = rational.mk((2, 8))
            r2 = rational.mk((1, 4))
            res = rational.sub((r1, r2))
            assert res.numerator == sp.int(0)

        @sp.private
        def test_rational_mul(self):
            r1 = rational.mk((2, 5))
            r2 = rational.mk((3, 4))
            res = rational.mul((r1, r2))
            assert res.numerator == sp.int(3)
            assert res.denominator == sp.nat(10)
            r1 = rational.mk((-4, 6))
            r2 = rational.mk((1, 4))
            res = rational.mul((r1, r2))
            assert res.numerator == sp.int(-1)
            assert res.denominator == sp.nat(6)

        @sp.private
        def test_rational_div(self):
            r1 = rational.mk((2, 5))
            r2 = rational.mk((3, 4))
            res = rational.div((r1, r2))
            assert res.numerator == sp.int(8)
            assert res.denominator == sp.nat(15)
            r1 = rational.mk((7, 4))
            r2 = rational.mk((2, 7))
            res = rational.div((r1, r2))
            assert res.numerator == sp.int(49)
            assert res.denominator == sp.nat(8)

        @sp.entrypoint
        def ep(self):
            self.test_rational()
            self.test_ceil()
            self.test_floor()
            self.test_rational_add()
            self.test_rational_sub()
            self.test_rational_mul()
            self.test_round()


@sp.add_test()
def test():
    s = sp.test_scenario("Test")
    c = M.C()
    s += c
    c.ep()
