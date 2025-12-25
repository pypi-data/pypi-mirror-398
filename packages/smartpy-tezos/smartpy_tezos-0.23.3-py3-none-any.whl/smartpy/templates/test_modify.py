import smartpy as sp


@sp.module
def main():
    t2: type = sp.record(a=sp.nat, b=sp.int, c=sp.bool, d=sp.string).layout(
        ("a", ("b", ("c", "d")))
    )
    t3: type = sp.record(a=sp.nat, b=sp.int, c=sp.bool, d=sp.string).layout(
        ((("a", "b"), "c"), "d")
    )
    t4: type = sp.record(a=sp.nat, b=sp.int, c=sp.bool, d=sp.string).layout(
        (("a", "b"), ("c", "d"))
    )

    class C1(sp.Contract):
        def __init__(self):
            self.data.x1 = sp.record(a=sp.nat(0), b=sp.int(1), c=True, d="abc")
            self.data.x2 = sp.record(a=sp.nat(0), b=sp.int(1), c=True, d="abc")
            self.data.x3 = sp.record(a=sp.nat(0), b=sp.int(1), c=True, d="abc")
            self.data.x4 = sp.record(a=sp.nat(0), b=sp.int(1), c=True, d="abc")
            self.data.y = (sp.nat(0), sp.int(1), True, "abc")
            self.data.z = sp.record(
                a=sp.nat(0), b=sp.int(1), c=True, d=sp.record(e=1, f="x")
            )

        @sp.entrypoint
        def ep1(self):
            sp.cast(self.data.x2, t2)
            sp.cast(self.data.x3, t3)
            sp.cast(self.data.x4, t4)
            with sp.modify_record(self.data.x1) as x1:
                assert abs(x1.b) == x1.a + 1
            with sp.modify_record(self.data.x2) as x2:
                assert abs(x2.b) == x2.a + 1
                x2.d = "xyz"
            with sp.modify_record(self.data.x3) as x3:
                assert abs(x3.b) == x3.a + 1
                x3.d = "xyz"
            with sp.modify_record(self.data.x4) as x4:
                assert abs(x4.b) == x4.a + 1
                x4.d = "xyz"

        @sp.entrypoint
        def ep2(self):
            with sp.modify_record(self.data.x1) as data:
                assert abs(data.b) == data.a + 1
                data.d = "xyz"

        @sp.entrypoint
        def ep4(self):
            with sp.modify_record(self.data.x1) as data:
                _ = data.a

        @sp.entrypoint
        def ep5(self):
            with sp.modify_record(self.data.x1) as data:
                assert abs(data.b) == data.a + 1
                data.d = "xyz"
            self.data.x1.a += 5

        @sp.entrypoint
        def ep5(self, alice):
            with sp.modify_record(self.data.x1) as data:
                sp.send(alice, sp.tez(0))
                data.d = "xyz"
            self.data.x1.a += 5

        @sp.entrypoint
        def ep6(self):
            with sp.modify_record(self.data.z) as outter:
                with sp.modify_record(outter.d) as inner:
                    outter.b = 100
                    inner.e = 2
                    inner.f = "y"

        @sp.entrypoint
        def ep7(self):
            assert self.data.z.d.e == 2
            with sp.modify_record(self.data.z.d) as z_d:
                assert z_d.e == 2
                z_d.e = 3
                z_d.f = "z"
                assert z_d.e == 3
                z_d.e = 4
                assert z_d.e == 4
            assert self.data.z.d.e == 4

    class C2(sp.Contract):
        def __init__(self):
            self.data.a = sp.nat(0)
            self.data.b = sp.int(1)
            self.data.c = True
            self.data.d = "abc"

        @sp.entrypoint
        def ep1(self):
            with sp.modify_record(self.data) as data:
                assert abs(data.b) == data.a + 1
                data.d = "xyz"

        @sp.entrypoint
        def ep2(self):
            with sp.modify_record(self.data) as data:
                data.d = "abc"


@sp.add_test()
def test():
    alice = sp.test_account("Alice")
    s = sp.test_scenario("Match")
    c1 = main.C1()
    s += c1
    c1.ep1()
    c1.ep2()
    c1.ep4()
    c1.ep5()
    c1.ep6()
    c1.ep7()

    s += main.C2()
