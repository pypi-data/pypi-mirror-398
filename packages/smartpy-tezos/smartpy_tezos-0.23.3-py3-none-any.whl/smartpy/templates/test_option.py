import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        def __init__(self):
            self.data.x = sp.Some(sp.int(42))

        @sp.entrypoint
        def set(self, x):
            self.data.x = x

        @sp.entrypoint
        def map(self, f):
            self.data.x = map(f, self.data.x)

    def f1(x):
        return x + 1

    def f2(x):
        return x + 2

    def f3(x):
        return x - 1


@sp.add_test()
def test():
    s = sp.test_scenario("Test")
    c = main.C()
    s += c
    c.map(main.f1)
    s.verify(c.data.x == sp.Some(43))
    c.map(main.f2)
    s.verify(c.data.x == sp.Some(45))

    c.set(None)
    c.map(main.f3)
    s.verify(c.data.x == None)
