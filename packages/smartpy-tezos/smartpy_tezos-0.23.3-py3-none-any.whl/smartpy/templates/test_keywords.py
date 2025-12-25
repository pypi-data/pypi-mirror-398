import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        def __init__(self, x, y):
            self.data.x = x
            self.data.y = y


@sp.add_test()
def test():
    s = sp.test_scenario("Keywords")
    c = main.C(y=42, x="abc")
    s += c
    s.verify(c.data.x == "abc")
    s.verify(c.data.y == 42)
