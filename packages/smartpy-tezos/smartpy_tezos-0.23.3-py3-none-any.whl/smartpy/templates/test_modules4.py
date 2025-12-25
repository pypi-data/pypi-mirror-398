import smartpy as sp


@sp.module
def main():
    class A(sp.Contract):
        def __init__(self, x):
            self.data.a = 42

    class C(sp.Contract):
        pass

    class D(A, C):
        def __init__(self, x):
            A.__init__(self, x)
            C.__init__(self)


@sp.add_test()
def test():
    s = sp.test_scenario("Test")

    d = main.D(0)
    s += d
