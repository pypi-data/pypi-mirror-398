import smartpy as sp


@sp.module
def main():
    class Created(sp.Contract):
        def __init__(self, a: sp.int, b: sp.nat):
            self.data.a = a
            self.data.b = b

        @sp.entrypoint
        def myEntryPoint(self, params):
            self.data.a += params.x
            self.data.b += params.y

    class MyContract(sp.Contract):
        def __init__(self):
            self.data.value = 0
            self.data.ggg = sp.Some(42)
            self.data.fff = None
            self.data.abcd = 0
            self.data.f = lambda x: x + 1

        @sp.entrypoint
        def f(self):
            toto = lambda x: sp.fst(x) + sp.snd(x)
            titi = toto.apply(5)
            self.data.value = titi(8)

        @sp.entrypoint
        def flambda(self):
            self.data.value = self.flam(self.flam(15)) + self.square_root(12345)

        @sp.private()
        def flam(self, params):
            return 322 * params

        @sp.private()
        def square_root(self, x):
            assert x >= 0
            y = x
            while y * y > x:
                y = (x / y + y) / 2
            assert (y * y <= x) and (x < (y + 1) * (y + 1))
            return y

        @sp.private()
        def comp(self, params):
            return params.f(params.x)

        @sp.entrypoint
        def comp_test(self):
            self.data.abcd = self.comp(sp.record(f=lambda x: x + 3, x=2))

        @sp.private()
        def abs(self, x):
            if x > 0:
                return x
            else:
                return -x

        @sp.entrypoint
        def abs_test(self, x):
            self.data.abcd = self.abs(x)

        @sp.entrypoint
        def h(self):
            def sqrt(x):
                assert x >= 0
                y = x
                while y * y > x:
                    y = (x / y + y) / 2
                assert y * y <= x and x < (y + 1) * (y + 1)
                return y

            self.data.fff = sp.Some(sqrt)

        @sp.entrypoint
        def hh(self, params):
            self.data.value = self.data.fff.unwrap_some()(params)

        @sp.entrypoint
        def i(self):
            def ch1(x):
                assert x >= 0

            def ch2(x):
                assert x >= 0
                return x - 2

            def ch3(x):
                assert x >= 0
                return True

            def ch4(x):
                def check3bis(x):
                    assert x >= 0
                    return False

                assert x >= 0
                return 3 * x

            self.data.value = ch4(12)
            assert self.not_pure() == self.data.value

        @sp.entrypoint
        def operation_creation(self):
            @sp.effects(with_operations=True)
            def test(x):
                _ = sp.create_contract(Created, None, sp.tez(0), sp.record(a=x, b=15))
                _ = sp.create_contract(
                    Created, None, sp.tez(0), sp.record(a=2 * x, b=15)
                )

            f = test
            f(12345001)
            f(12345002)

        @sp.entrypoint
        def operation_creation_result(self):
            @sp.effects(with_operations=True)
            def test(x):
                _ = sp.create_contract(Created, None, sp.tez(0), sp.record(a=x, b=15))
                return 4

            f = test
            x = f(12345001)
            y = f(12345002)
            sum = x + y

        @sp.entrypoint
        def managed_operation_creation(self):
            @sp.effects()
            def test(x):
                ops = []
                r = sp.create_contract_operation(
                    Created, None, sp.tez(0), sp.record(a=x, b=15)
                )
                ops.push(r.operation)
                r = sp.create_contract_operation(
                    Created, None, sp.tez(0), sp.record(a=2 * x, b=15)
                )
                ops.push(r.operation)
                return ops

            f = test
            ops = f(12345001)
            for op in reversed(ops):
                sp.operations.push(op)
            ops = f(12345002)
            for op in reversed(ops):
                sp.operations.push(op)

        # @sp.private()
        # def oh_no(self, params):
        #     with sp.set_result_type(sp.int):
        #     if params > 0:
        #         sp.failwith("too big")
        #     else:
        #         sp.failwith("too small")

        @sp.private(with_storage="read-write")
        def not_pure(self, x):
            return self.data.value

        # @sp.entrypoint
        # def fact(self, n):
        #     fact = sp.compute(sp.build_lambda((lambda n, fact: sp.eif(n<=1,1,n*fact(n-1))), recursive=True))
        #     self.data.abcd = fact(n)

    c1: type = sp.pair[sp.nat, sp.unit]
    c2: type = sp.pair[sp.address, c1]
    c3: type = sp.pair[sp.bool, c2]
    c4: type = sp.pair[sp.int, c3]
    t_record: type = sp.record(a=sp.int, b=sp.bool, c=sp.address, d=sp.nat, e=sp.unit)

    def format_record(param):
        sp.cast(param, c4)
        (a, p2) = param
        (b, p3) = p2
        (c, p4) = p3
        (d, e) = p4
        return sp.cast(sp.record(a=a, b=b, c=c, d=d, e=e), t_record)

    class C2(sp.Contract):
        def __init__(self):
            self.data.value = sp.cast(None, sp.option[t_record])
            l1 = format_record.apply(1)
            l2 = l1.apply(True)
            l3 = l2.apply(sp.address("tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"))
            l4 = l3.apply(2)
            self.data.l1 = l1
            self.data.l2 = l2
            self.data.l3 = l3
            self.data.l4 = l4

        @sp.entrypoint
        def exec_l1(self):
            self.data.value = sp.Some(
                self.data.l1(
                    (
                        True,
                        (sp.address("tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"), (2, ())),
                    )
                )
            )

        @sp.entrypoint
        def exec_l2(self):
            self.data.value = sp.Some(
                self.data.l2(
                    (sp.address("tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"), (2, ()))
                )
            )

        @sp.entrypoint
        def exec_l3(self):
            self.data.value = sp.Some(self.data.l3((2, ())))

        @sp.entrypoint
        def exec_l4(self):
            self.data.value = sp.Some(self.data.l4())

    def f(param: sp.pair[sp.int, sp.int]):
        (a, b) = param
        return a + b


@sp.add_test()
def test():
    scenario = sp.test_scenario("Lambdas")
    scenario.h1("Lambdas")
    c1 = main.MyContract()
    scenario += c1
    c1.f()
    c1.flambda()
    c1.i()
    c1.comp_test()
    c1.abs_test(5)
    scenario.verify(c1.data.abcd == 5)
    c1.abs_test(-42)
    scenario.verify(c1.data.abcd == 42)
    # c1.fact(3)
    # scenario.verify(c1.data.abcd == 6)
    # c1.fact(5)
    # scenario.verify(c1.data.abcd == 120)

    c2 = main.C2()
    scenario += c2
    c2.exec_l1()
    c2.exec_l2()
    c2.exec_l3()
    c2.exec_l4()

    g = main.f.apply(5)
    scenario.verify(g(7) == 12)
