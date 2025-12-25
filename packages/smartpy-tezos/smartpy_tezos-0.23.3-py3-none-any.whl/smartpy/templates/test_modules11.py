import smartpy as sp


@sp.module
def aux():
    class A(sp.Contract):
        def __init__(self, a):
            self.data.a = a

        @sp.entrypoint
        def double_a(self):
            self.data.a *= 2

    class B(sp.Contract):
        def __init__(self, b):
            self.data.b = b

        @sp.entrypoint
        def double_b(self):
            self.data.b *= 2


@sp.module
def main():
    import aux

    class C(aux.A, aux.B):
        def __init__(self, a, b):
            aux.A.__init__(self, a)
            aux.B.__init__(self, b)
            self.data.c = a + b


@sp.add_test()
def test():
    s = sp.test_scenario("Test")

    c = main.C(2, 3)
    s += c
    s.verify(c.data.a == 2)
    s.verify(c.data.b == 3)
    s.verify(c.data.c == 5)

    c.double_a()
    s.verify(c.data.a == 4)
    s.verify(c.data.b == 3)
    s.verify(c.data.c == 5)

    c.double_b()
    s.verify(c.data.a == 4)
    s.verify(c.data.b == 6)
    s.verify(c.data.c == 5)
