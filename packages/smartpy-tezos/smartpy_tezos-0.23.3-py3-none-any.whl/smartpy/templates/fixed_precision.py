# Fixed precision computations - Example for illustrative purposes only.

import smartpy as sp

"""
This has been inspired by

https://github.com/Sophia-Gold/michelson/blob/master/log2fix.tz

http://www.claysturner.com/dsp/BinaryLogarithm.pdf

1) Initialize result to 0: y = 0.
2)Initialize mantissa-bit decimal value to 0.5: b = 1/2.

3) While x < 1, x = 2x, y = y - 1.
4) While x >= 2, x = x/2, y = y + 1.

6)Square: x = x * x.
7) If x > 2, x = x/2, y = y + b.
8) Scale for next bit: b = b/2.
9)Go to Step 6 and repeat until desired number of mantissa bits are found.

10) Final log(x) value: y.
"""


@sp.module
def main():
    class MyContract(sp.Contract):
        def __init__(self, precision: sp.nat):
            self.private.precision = precision
            self.data.value = 0

        @sp.entrypoint
        def log(self, params):
            assert params != 0
            y = 0
            x = params
            while x < 1 << self.private.precision:
                x <<= 1
                y -= sp.to_int(1 << self.private.precision)
            while x >= 2 << self.private.precision:
                x >>= 1
                y += sp.to_int(1 << self.private.precision)
            b = 1 << sp.as_nat(self.private.precision - 1)
            while 0 < b:
                x = (x * x) >> self.private.precision
                if x > 2 << self.private.precision:
                    x >>= 1
                    y += sp.to_int(b)
                b >>= 1
            self.data.value = y


def direct(x, precision):
    import math

    return int((math.log(x / (1 << precision)) / math.log(2)) * (1 << precision))


@sp.add_test()
def test():
    scenario = sp.test_scenario("FixedPrecision")
    scenario.h1("Fixed Precision Computations")
    c1 = main.MyContract(precision=16)
    scenario += c1

    def check_ok(scenario, n):
        d = direct(n, 16)
        scenario.h3("Computing log(%i / 65536)" % n)
        scenario.p("Direct computation %i" % direct(n, 16))
        c1.log(n)
        scenario.verify(abs(c1.data.value - d) < 2)

    check_ok(scenario, 1000000)
    check_ok(scenario, 65535)
    check_ok(scenario, 65536)
    check_ok(scenario, 65537)
    check_ok(scenario, 131071)
    check_ok(scenario, 131072)
    check_ok(scenario, 131073)
    check_ok(scenario, 1)
