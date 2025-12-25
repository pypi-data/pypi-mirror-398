import smartpy as sp

# Sets


@sp.module
def m1():
    class C(sp.Contract):
        def __init__(self):
            self.data.l = sp.cast([], sp.list[sp.int])
            self.data.rl = sp.cast([], sp.list[sp.int])

        @sp.entrypoint
        def test(self, s):
            self.data.l = s.elements()
            self.data.rl = reversed(s.elements())


sc = sp.test_scenario("test_deprecated_set_syntax")
c1 = m1.C()
sc += c1
c1.test(sp.set([1, 12, 100]))
sc.verify_equal(c1.data.l, [1, 12, 100])
sc.verify_equal(c1.data.rl, [100, 12, 1])
