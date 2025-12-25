import smartpy as sp


@sp.module
def M():
    import smartpy.stdlib.math as math

    class C(sp.Contract):
        def __init__(self):
            pass

        @sp.private
        def test_pow(self):
            assert math.pow((2, 0)) == sp.int(1)
            assert math.pow((2, 1)) == sp.int(2)
            assert math.pow((2, 3)) == sp.int(8)
            assert math.pow((3, 0)) == sp.int(1)
            assert math.pow((3, 1)) == sp.int(3)
            assert math.pow((3, 2)) == sp.int(9)
            assert math.pow((3, 3)) == sp.int(27)
            assert math.pow((10, 0)) == sp.int(1)
            assert math.pow((10, 1)) == sp.int(10)
            assert math.pow((10, 2)) == sp.int(100)
            assert math.pow((10, 3)) == sp.int(1000)

        @sp.private
        def test_gcd(self):
            assert math.gcd((15, 10)) == sp.int(5)
            assert math.gcd((18, 42)) == sp.int(6)
            assert math.gcd((15, 36)) == sp.int(3)
            assert math.gcd((4, 24)) == sp.int(4)
            assert math.gcd((-4, 24)) == sp.int(4)

        @sp.private
        def test_lcm(self):
            assert math.lcm((3, 5)) == sp.int(15)
            assert math.lcm((54, 24)) == sp.int(216)

        @sp.entrypoint
        def ep(self):
            self.test_pow()
            self.test_gcd()
            self.test_lcm()


@sp.add_test()
def test():
    s = sp.test_scenario("Test")
    c = M.C()
    s += c
    c.ep()
