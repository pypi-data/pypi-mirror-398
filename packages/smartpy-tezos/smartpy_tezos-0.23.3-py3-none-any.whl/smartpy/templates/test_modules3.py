import smartpy as sp


@sp.module
def main():
    class A(sp.Contract):
        def __init__(self, x):
            self.data.a = 42
            self.data.x = x

        @sp.entrypoint
        def ep1(self, x):
            self.data.x = 42
            assert x == "abc"

        @sp.entrypoint
        def ep2(self, x):
            self.data.x = 42
            assert x == "abc"

        @sp.private(with_storage="read-write")
        def f(self, x):
            self.data.a = 123
            return x + 1

    class B(A):
        def __init__(self, yy):
            A.__init__(self, 2 * yy)
            self.data.y = self.data.x + yy

        @sp.entrypoint
        def ep3(self, x):
            assert self.f(x) == 43

    class B2(A):
        def __init__(self, yy):
            A.__init__(self, 2 * yy)
            self.data.xx = 0

    class C(sp.Contract):
        pass

    class D(A, C):
        def __init__(self):
            A.__init__(self, 1)
            C.__init__(self)
            self.data.y = 1000

        @sp.entrypoint
        def ep4(self, x):
            assert x == 42


@sp.add_test()
def test():
    s = sp.test_scenario("Test")

    a = main.A(123)
    s += a
    s.verify(a.data == sp.record(a=42, x=123))

    b = main.B(3)
    s += b
    s.verify(b.data == sp.record(a=42, x=2 * 3, y=6 + 3))
    b.ep3(42)
    s.verify(b.data == sp.record(a=123, x=2 * 3, y=6 + 3))

    b2 = main.B(3)
    s += b2
    s.verify(b2.data == sp.record(a=42, x=2 * 3, y=6 + 3))

    d = main.D()
    s += d
    d.ep4(42)
    s.verify(d.data == sp.record(a=42, x=1, y=1000))

    c = s.compute(123)
    a = main.A(c)
    s += a
