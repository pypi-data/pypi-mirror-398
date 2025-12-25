import smartpy as sp


@sp.module
def main():
    shape: type = sp.variant(Circle=sp.int, Rectangle=sp.pair[sp.int, sp.int])

    class Aux(sp.Contract):
        @sp.entrypoint
        def default(self, x):
            assert x == sp.int(100)

    class C(sp.Contract):
        def __init__(self):
            self.data.s = 0
            self.data.value = 3

        @sp.entrypoint
        def ep1(self, x, y):
            r = x * x + y * y
            assert r == 25

        @sp.entrypoint
        def ep2(self, x):
            if x > 42:
                raise "too big"

        @sp.entrypoint
        def ep3(self, x):
            pass
            assert x <= 42
            self.data.s = x

        @sp.entrypoint
        def myEntryPoint(self, params):
            assert self.data.s <= 123
            self.data.s += params

        @sp.entrypoint
        def multiply(self, x, y):
            self.data.value = x * y

        @sp.entrypoint
        def add(self, x, y):
            self.data.value = x + y

        @sp.entrypoint
        def square(self, x):
            self.data.value = x * x

        @sp.entrypoint
        def test_layout(self, x):
            sp.cast(x, sp.record(a=int, b=sp.string, c=bool).layout((("a", "c"), "b")))

        @sp.entrypoint
        def squareRoot(self, x):
            assert x >= 0
            y = 42
            while y * y > x:
                y = (x / y + y) / 2
            assert y * y <= x and x < (y + 1) * (y + 1)
            self.data.value = y

        @sp.entrypoint
        def strings_and_bytes(self):
            assert "abc" == "abc"
            assert sp.slice(3, 5, "0123456789") == sp.Some("34567")
            assert sp.slice(3, 5, "01234") == None
            assert sp.bytes("0xaBcd") == sp.bytes("abcd")

            assert sp.slice(3, 5, "0123456789") == sp.Some("34567")
            assert sp.slice(3, 5, "01234") == None

            assert sp.slice(3, 5, sp.bytes("0x00010203040506070809")) == sp.Some(
                sp.bytes("0x0304050607")
            )
            assert sp.slice(3, 5, sp.bytes("0x0001020304")) == None

            assert "ab" + "c" == "abc"
            assert sp.concat(["ab", "cd", "ef"]) == "abcdef"
            assert sp.concat(
                [sp.bytes("ab"), sp.bytes("cd"), sp.bytes("ef")]
            ) == sp.bytes("abcdef")

        @sp.entrypoint
        def tuples_and_records(self):
            assert sp.fst((1, "abc")) == 1
            (a, b, c) = (42, "abc", True)
            assert a == 42
            assert b == "abc"
            assert c == True
            x = sp.record(a=42, b="abc")
            sp.cast(x, sp.record(a=sp.int, b=sp.string))

        @sp.entrypoint
        def options_and_variants(self):
            assert not sp.cast(None, sp.option[sp.int]).is_some()
            assert sp.Some(42).is_some()
            assert sp.cast(None, sp.option[sp.int]).is_none()
            assert not sp.Some(42).is_none()

            c = sp.variant.Circle(2)
            assert c.is_variant.Circle()
            assert c.unwrap.Circle() == 2

        @sp.entrypoint
        def lists_sets_and_maps(self):
            l = [1, 2, 3]
            s = {1, 2, 3}
            m = {"a": 65, "b": 66}
            assert s.contains(1)
            assert len(l) == 3
            assert len(s) == 3
            assert len(m) == 2
            assert len(l) == 3
            assert len(s) == 3
            assert len(m) == 2
            assert sum([1, 2, 3]) == 6
            assert sum(sp.cons(1, [2, 3])) == 6
            # assert m.items() ==
            assert sum(m.values()) == 131
            assert sp.concat(m.keys()) == "ab"
            assert sp.pack(range(7)) == sp.pack([0, 1, 2, 3, 4, 5, 6])
            assert sp.pack(range(3, 7)) == sp.pack([3, 4, 5, 6])
            assert sp.pack(range(3, 7, 2)) == sp.pack([3, 5])
            assert m.get("xyz", default=100) == 100
            m = {"a": 65, "b": 66}
            del m["a"]
            assert not m.contains("a")
            assert not s.contains(4)
            s.add(4)
            assert s.contains(4)

        @sp.entrypoint
        def lambdas(self):
            @sp.effects(with_storage="read-write")
            def f(x):
                self.data.s = 42
                return x

            assert f(42) == 42

        @sp.entrypoint
        def abc(self, x):
            assert x == 42

        @sp.entrypoint
        def operations(self, address):
            sp.set_delegate(None)
            sp.emit("Hello")
            sp.emit("World", tag="mytag")
            sp.emit(sp.record(a="ABC", b="XYZ"), tag="mytag2")
            sp.emit(sp.record(a="ABC", b="XYZ"), tag="mytag2", with_type=False)
            sp.transfer(42, sp.mutez(0), sp.self_entrypoint("abc"))
            c = sp.contract(sp.int, address).unwrap_some()
            sp.transfer(100, sp.mutez(0), c)

        @sp.entrypoint
        def arithmetic(self):
            assert sp.ediv(14, 3) == sp.Some((4, 2))
            assert sp.ediv(-14, 3) == sp.Some((-5, 1))
            assert sp.ediv(14, -3) == sp.Some((-4, 2))  # -4 * -3 + 2 ==  14
            assert sp.ediv(-14, -3) == sp.Some((5, 1))  #  5 * -3 + 1 == -14
            assert 14 / 3 == 4
            assert -14 / 3 == -5
            assert 14 / -3 == -4  # -4 * -3 + 2 ==  14
            assert -14 / -3 == 5  #  5 * -3 + 1 == -14
            assert -4 * -3 + 2 == 14
            assert 5 * -3 + 1 == -14
            assert sp.nat(2) - sp.nat(3) == -1
            assert -sp.nat(2) == sp.int(-2)
            assert sp.is_nat(2) == sp.Some(2)
            assert sp.is_nat(-2) == None
            assert sp.as_nat(2) == 2
            assert sp.to_int(2) == 2
            assert sp.to_int(sp.nat(2)) == sp.to_int(2)
            assert sp.to_int(2) == 2
            assert sp.mutez(2) == sp.mutez(2)
            assert sp.mutez(2) + sp.mutez(2) == sp.mutez(4)
            assert sp.mutez(10) - sp.mutez(8) == sp.mutez(2)
            assert sp.split_tokens(sp.mutez(100), 1, 20) == sp.mutez(5)
            assert sp.split_tokens(sp.mutez(100), 2, 20) == sp.mutez(10)
            assert sp.split_tokens(sp.mutez(101), 1, 20) == sp.mutez(5)
            assert sp.split_tokens(sp.mutez(101), 2, 20) == sp.mutez(10)
            assert 42 & 1 == 0
            assert 42 | 1 == 43
            assert not 42 == 43
            assert True or 1 / 0 == 42
            assert not (False and (1 / 0 == 42))
            assert sp.split_tokens(sp.mutez(100), 20, 30) == sp.mutez(66)
            assert 8 / 3 == 2
            assert -8 / 3 == -3
            assert 8 / -3 == -2  # -2 * -3 + 2 == 8
            assert -8 / -3 == 3  #  3 * -3 + 1 == 8
            a1 = sp.int(8)
            b1 = sp.int(3)
            assert sp.cast(
                sp.ediv(a1, b1), sp.option[sp.pair[sp.int, sp.nat]]
            ) == sp.Some((2, 2))
            a2 = sp.int(8)
            b2 = sp.nat(3)
            assert sp.cast(
                sp.ediv(a2, b2), sp.option[sp.pair[sp.int, sp.nat]]
            ) == sp.Some((2, 2))
            a3 = sp.nat(8)
            b3 = sp.int(3)
            assert sp.cast(
                sp.ediv(a3, b3), sp.option[sp.pair[sp.int, sp.nat]]
            ) == sp.Some((2, 2))
            a4 = sp.nat(8)
            b4 = sp.nat(3)
            assert sp.cast(
                sp.ediv(a4, b4), sp.option[sp.pair[sp.nat, sp.nat]]
            ) == sp.Some((2, 2))
            assert sp.cast(sp.ediv(a4, b4), sp.option[sp.pair[sp.nat, sp.nat]]) != None


@sp.add_test()
def test():
    s = sp.test_scenario("Parsed")
    c = main.C()
    s += c

    c.ep1(x=3, y=4)
    c.ep1(x=3, y=5, _valid=False)

    c.ep2(10)
    c.ep2(100, _valid=False)

    c.ep3(10)
    s.verify(c.data.s == 10)
    c.ep3(100, _valid=False)

    c.arithmetic()
    c.strings_and_bytes()
    c.tuples_and_records()
    c.options_and_variants()
    c.lists_sets_and_maps()
    c.lambdas()

    aux = main.Aux()
    s += aux
    c.operations(aux.address)
