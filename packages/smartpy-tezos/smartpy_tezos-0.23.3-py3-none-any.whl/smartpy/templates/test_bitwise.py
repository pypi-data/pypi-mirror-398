import smartpy as sp


@sp.module
def main():
    class Test(sp.Contract):
        def __init__(self):
            self.data.n = sp.nat(1234567)
            self.data.i = sp.int(3)
            self.data.b = sp.bytes("0xf6")

        @sp.entrypoint
        def test_and(self, x):
            self.data.n = self.data.n & x

        @sp.entrypoint
        def test_or(self, x):
            self.data.n = self.data.n | x

        @sp.entrypoint
        def test_exclusive_or(self, x):
            self.data.n = self.data.n ^ x

        @sp.entrypoint
        def test_shift_right(self, x):
            self.data.n = self.data.n >> x

        @sp.entrypoint
        def test_shift_left(self, x):
            self.data.n = self.data.n << x

        @sp.entrypoint
        def test_invert(self, params):
            sp.cast(params.b, sp.bytes)
            sp.cast(params.i, sp.int)
            self.data.b = sp.invert_bytes(params.b)
            self.data.i = ~params.i

        @sp.entrypoint
        def test_nat_to_bytes(self, x):
            sp.cast(x, sp.nat)
            self.data.b = sp.to_bytes(x)

        @sp.entrypoint
        def test_bytes_to_nat(self, x):
            sp.cast(x, sp.bytes)
            self.data.n = sp.to_nat(x)

        @sp.entrypoint
        def test_int_to_bytes(self, x):
            sp.cast(x, sp.int)
            self.data.b = sp.to_bytes(x)

        @sp.entrypoint
        def test_bytes_to_int(self, x):
            sp.cast(x, sp.bytes)
            self.data.i = sp.to_int(x)

        @sp.entrypoint
        def test_shift_left_bytes(self, x):
            self.data.b = sp.lshift_bytes(self.data.b, x)

        @sp.entrypoint
        def test_shift_right_bytes(self, x):
            self.data.b = sp.rshift_bytes(self.data.b, x)

        @sp.entrypoint
        def test_and_bytes(self, x):
            self.data.b = sp.and_bytes(self.data.b, x)

        @sp.entrypoint
        def test_or_bytes(self, x):
            self.data.b = sp.or_bytes(self.data.b, x)

        @sp.entrypoint
        def test_xor_bytes(self, x):
            self.data.b = sp.xor_bytes(self.data.b, x)


@sp.add_test()
def test():
    scenario = sp.test_scenario("test")
    c1 = main.Test()
    scenario += c1
    c1.test_and(10)
    scenario.verify(c1.data.n == 2)
    c1.test_or(10)
    scenario.verify(c1.data.n == 10)
    c1.test_exclusive_or(9)
    scenario.verify(c1.data.n == 3)
    c1.test_shift_left(10)
    scenario.verify(c1.data.n == 3072)
    c1.test_shift_right(10)
    scenario.verify(c1.data.n == 3)

    c1.test_invert(sp.record(b=sp.bytes("0xf6"), i=100))
    scenario.verify(c1.data.b == sp.bytes("0x09"))
    scenario.verify(c1.data.i == -101)

    c1.test_invert(sp.record(b=sp.bytes("0x00"), i=0))
    scenario.verify(c1.data.b == sp.bytes("0xff"))
    scenario.verify(c1.data.i == -1)

    c1.test_invert(sp.record(b=sp.bytes("0x80"), i=-100))
    scenario.verify(c1.data.b == sp.bytes("0x7f"))
    scenario.verify(c1.data.i == 99)

    c1.test_nat_to_bytes(0)
    scenario.verify(c1.data.b == sp.bytes("0x"))

    c1.test_nat_to_bytes(255)
    scenario.verify(c1.data.b == sp.bytes("0xff"))

    c1.test_nat_to_bytes(256)
    scenario.verify(c1.data.b == sp.bytes("0x0100"))

    c1.test_bytes_to_nat(sp.bytes("0x7f"))
    scenario.verify(c1.data.n == 127)

    c1.test_bytes_to_nat(sp.bytes("0xff"))
    scenario.verify(c1.data.n == 255)

    c1.test_bytes_to_nat(sp.bytes("0x00ff"))
    scenario.verify(c1.data.n == 255)

    c1.test_bytes_to_nat(sp.bytes("0x000000ff"))
    scenario.verify(c1.data.n == 255)

    c1.test_int_to_bytes(0)
    scenario.verify(c1.data.b == sp.bytes("0x"))

    c1.test_int_to_bytes(255)
    scenario.verify(c1.data.b == sp.bytes("0x00ff"))

    c1.test_int_to_bytes(256)
    scenario.verify(c1.data.b == sp.bytes("0x0100"))

    c1.test_int_to_bytes(-5)
    scenario.verify(c1.data.b == sp.bytes("0xfb"))

    c1.test_int_to_bytes(-260)
    scenario.verify(c1.data.b == sp.bytes("0xfefc"))

    c1.test_int_to_bytes(127)
    scenario.verify(c1.data.b == sp.bytes("0x7f"))

    c1.test_int_to_bytes(128)
    scenario.verify(c1.data.b == sp.bytes("0x0080"))

    c1.test_int_to_bytes(-127)
    scenario.verify(c1.data.b == sp.bytes("0x81"))

    c1.test_int_to_bytes(-128)
    scenario.verify(c1.data.b == sp.bytes("0x80"))

    c1.test_bytes_to_int(sp.bytes("0xff"))
    scenario.verify(c1.data.i == -1)

    c1.test_bytes_to_int(sp.bytes("0x7f"))
    scenario.verify(c1.data.i == 127)

    c1.test_bytes_to_int(sp.bytes("0x007f"))
    scenario.verify(c1.data.i == 127)

    c1.test_bytes_to_int(sp.bytes("0x0000007f"))
    scenario.verify(c1.data.i == 127)

    c1.test_shift_left_bytes(10)
    scenario.verify(c1.data.b == sp.bytes("0x020000"))

    c1.test_shift_right_bytes(10)
    if scenario.simulation_mode() is sp.SimulationMode.MOCKUP:
        # mockups need this to be zero-padded
        scenario.verify(c1.data.b == sp.bytes("0x0080"))
    else:
        scenario.verify(c1.data.b == sp.bytes("0x80"))

    c1.test_and_bytes(sp.bytes("0x01"))
    scenario.verify(c1.data.b == sp.bytes("0x00"))

    c1.test_or_bytes(sp.bytes("0xf6"))
    scenario.verify(c1.data.b == sp.bytes("0xf6"))

    c1.test_xor_bytes(sp.bytes("0xf5"))  # 0b11110110 `xor` 0b11110101
    scenario.verify(c1.data.b == sp.bytes("0x03"))
