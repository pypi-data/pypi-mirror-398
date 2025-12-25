import smartpy as sp


@sp.module
def main():
    class A1(sp.Contract):
        def __init__(self, x):
            self.data.x = x

        @sp.private(with_storage="read-write")
        def f(self, _):
            self.data.x += 1

        @sp.entrypoint
        def ep(self):
            self.data.x += 10

    class A2(sp.Contract):
        def __init__(self, y):
            self.data.y = y

        @sp.private(with_storage="read-write")
        def f(self, _):
            self.data.y -= 1

        @sp.entrypoint
        def ep(self):
            self.data.y -= 10

    class B(A1, A2):
        def __init__(self, x, y):
            A1.__init__(self, x)
            if True:
                A2.__init__(self, y)
            else:
                A2.__init__(self, y)

        @sp.entrypoint
        def run_f(self):
            self.f()


@sp.add_test()
def test():
    s = sp.test_scenario("Test")

    a1 = main.A1(1000)
    s += a1
    s.verify(a1.data == sp.record(x=1000))
    a1.ep()
    s.verify(a1.data == sp.record(x=1010))

    a2 = main.A2(1020)
    s += a2
    s.verify(a2.data == sp.record(y=1020))
    a2.ep()
    s.verify(a2.data == sp.record(y=1010))

    b = main.B(1000, 1)
    s += b
    s.verify(b.data == sp.record(x=1000, y=1))
    b.ep()
    s.verify(b.data == sp.record(x=1010, y=1))
    b.run_f()
    s.verify(b.data == sp.record(x=1011, y=1))
