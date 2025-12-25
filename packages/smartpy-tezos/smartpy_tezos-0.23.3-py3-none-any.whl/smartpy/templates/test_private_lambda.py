import smartpy as sp


@sp.module
def main():
    class Lib(sp.Contract):
        @sp.private()
        def f(self, x):
            return x * 2

        @sp.private()
        def g(self, x):
            return x * 2

        @sp.private()
        def factorial(self, x):
            r = 1
            for y in range(2, x + 1):
                r *= y
            return r

        # @sp.private(recursive=True)
        # def factorial_rec(self, n, factorial_rec):
        #     sp.if n <= 1:
        #         return n
        #     sp.else:
        #         return n * factorial_rec(n-1)

        @sp.private()
        def factorial_five(self, params):
            sp.cast(params, sp.unit)
            r = 1
            for y in range(2, 6):
                r *= y
            return r

        @sp.entrypoint
        def test_factorial(self):
            assert self.factorial(5) == 120
            # assert self.factorial_rec(5) == 120
            assert self.factorial_five() == 120

        # @sp.private()
        # def failing(self, x):
        #     with sp.set_result_type(sp.int):
        #         raise "Aaa" + x

        # @sp.entrypoint
        # def test_failing(self):
        #     aaa = self.failing("")

    class Tester(sp.Contract):
        def __init__(self, f: sp.lambda_[sp.nat, sp.nat]):
            self.private.f = f
            self.data.x = None

        @sp.entrypoint
        def update(self, params):
            self.data.x = sp.Some(self.private.f(params))

        @sp.entrypoint
        def check(self, params, result):
            assert self.private.f(params) == result

    def f(x: sp.nat):
        return x * 2


@sp.add_test()
def test():
    s = sp.test_scenario("Bind")
    l = main.Lib()
    s += l
    l.test_factorial()
    # TODO activate this line when private lambda access is supported.
    # tester = main.Tester(l.f)
    tester = main.Tester(main.f)
    s += tester
    tester.update(12)
    s.verify(tester.data.x.unwrap_some() == 24)
    tester.check(params=12, result=24)
    tester.check(params=11, result=22)
