# Options and Variants - Example for illustrative purposes only.

import smartpy as sp


@sp.module
def main():
    class TestOptionsAndVariants(sp.Contract):
        def __init__(self):
            self.data.x = sp.variant.A(-1)
            self.data.y = sp.Some(-42)
            self.data.z = sp.Left(-10)
            self.data.r = 0
            self.data.s = sp.record(x=0, y=1)

        @sp.entrypoint
        def options(self):
            if self.data.y.is_some():
                self.data.r = 44 + self.data.y.unwrap_some(error="Not a some!")
                self.data.y = None
            else:
                self.data.r = 3
                self.data.y = sp.Some(12)

        @sp.entrypoint
        def ep1(self):
            match self.data.x:
                case A(arg):
                    self.data.x = sp.variant.B(-2)
                    self.data.r = arg
            self.data.x = sp.variant.C(3)

        @sp.entrypoint
        def ep3(self):
            match self.data.z:
                case Left(arg):
                    self.data.r = arg

        @sp.entrypoint
        def ep4(self):
            match self.data.x:
                case A(a1):
                    match self.data.z:
                        case Right(a2):
                            self.data.r = a1 + a2

        @sp.entrypoint
        def ep5(self):
            if self.data.x.is_variant.Toto():
                self.data.r = 42

        @sp.entrypoint
        def ep6(self):
            self.data.s = self.data.x.unwrap.Toto(error="no toto")

        @sp.entrypoint
        def ep7(self, params):
            self.data.x = params

        @sp.entrypoint
        def ep8(self, params):
            match params.x:
                case A(dummy):
                    self.data.x = params.x
                case B(arg):
                    self.data.y = sp.Some(12 + arg + params.y)

        @sp.entrypoint
        def ep9(self, params):
            sp.cast(params.other, int)
            match params.z:
                case A(dummy):
                    self.data.x = params.z


@sp.add_test()
def test():
    scenario = sp.test_scenario("variant")
    scenario.h1("Variants")
    c = main.TestOptionsAndVariants()
    scenario += c
    c.options()
    c.ep1()
    c.ep3()
    c.ep4()
    c.ep5()
    c.ep6(_valid=False)
