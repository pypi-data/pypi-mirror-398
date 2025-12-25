import smartpy as sp


@sp.module
def main():
    class A(sp.Contract):
        def __init__(self):
            self.data.x = 0

        @sp.private(with_storage="read-write")
        def aux(self, n):
            self.data.x += n

        @sp.private
        def gett(self):
            return 42

        @sp.entrypoint
        def ep(self):
            self.aux(1)

    class B(A):
        def __init__(self):
            A.__init__(self)
            self.data.y = 0

        # Override a private lambda
        @sp.private(with_storage="read-write")
        def aux(self, n):
            self.data.x += 100 * n

        @sp.entrypoint
        def ep2(self, n):
            self.aux(n)
            self.data.y += 1


@sp.add_test()
def test():
    s = sp.test_scenario("Test")

    a = main.A()
    s += a
    s.verify(a.data == sp.record(x=0))
    a.ep()
    s.verify(a.data == sp.record(x=1))

    b = main.B()
    s += b
    s.verify(b.data == sp.record(x=0, y=0))
    b.ep()
    s.verify(b.data == sp.record(x=100, y=0))
    b.ep2(5)
    s.verify(b.data == sp.record(x=600, y=1))
