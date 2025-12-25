import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        def __init__(self):
            self.data.r = 0

        @sp.entrypoint
        def ep(self, params):
            self.data.r = 1000 * (2 if params else 3)


@sp.add_test()
def test():
    s = sp.test_scenario("Match")
    c = main.C()
    s += c
    c.ep(True)
    s.verify(c.data.r == 2000)
    c.ep(False)
    s.verify(c.data.r == 3000)
