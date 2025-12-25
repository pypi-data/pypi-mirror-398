import sys

import smartpy as sp

# fix for issue #142 - name resolution of `A` and `f()` should work for derived classes


@sp.module
def main():
    class A(sp.Contract):
        pass

    def f():
        return 42

    class Creator(sp.Contract):
        @sp.entrypoint
        def create1(self):
            _ = f()
            _ = sp.create_contract(A, None, sp.mutez(123), ())


@sp.module
def main2():
    import main

    class CreatorSubclass(main.Creator):
        pass


# fix for issue #166 - name resolution of `f()` should work for derived classes in same module


@sp.module
def main3():
    def f():
        pass

    class C(sp.Contract):
        @sp.onchain_view()
        def g(self):
            return f()

    class C2(C):
        def __init__(self):
            C.__init__(self)


if "main" in __name__:

    @sp.add_test()
    def test():
        try:
            scenario = sp.test_scenario("Create", main2)
        except Exception as e:
            print("CAUGHT", e, file=sys.stderr)
            assert False

    @sp.add_test()
    def test2():
        try:
            _ = sp.test_scenario("T", main3)
        except Exception as e:
            print("CAUGHT", e, file=sys.stderr)
            assert False


@sp.module
def cm():
    import smartpy.stdlib.utils as utils

    class Calculator(sp.Contract):
        def __init__(self):
            self.data.i = utils.mutez_to_nat(sp.mutez(10))


@sp.module
def inherit_from_contract_with_imports():
    import cm

    class CalculatorNew(cm.Calculator):
        def __init__(self):
            cm.Calculator.__init__(self)


if "main" in __name__:

    @sp.add_test()
    def test3():
        try:
            scenario = sp.test_scenario(
                "inherit_from_contract_with_imports",
                inherit_from_contract_with_imports,
            )
        except Exception as e:
            print("CAUGHT", e, file=sys.stderr)
            assert False


@sp.module
def inherit_from_contract_with_imports2():
    import smartpy.templates.calculator_main as m

    class CalculatorNew(m.Calculator):
        def __init__(self):
            m.Calculator.__init__(self)


if "main" in __name__:

    @sp.add_test()
    def test4():
        try:
            scenario = sp.test_scenario(
                "inherit_from_contract_with_imports2",
                inherit_from_contract_with_imports2,
            )
        except Exception as e:
            print("CAUGHT", e, file=sys.stderr)
            assert False
