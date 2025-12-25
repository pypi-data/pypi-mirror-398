import smartpy as sp


@sp.module
def M():
    import smartpy.stdlib.fixed_point as fp
    import smartpy.stdlib.rational as rational
    import smartpy.stdlib.string_utils as su

    class C(sp.Contract):
        def __init__(self):
            pass

        @sp.private
        def test_drop_first(self):
            assert su.drop_first((0, "abc")) == sp.Some("abc")
            assert su.drop_first((1, "abc")) == sp.Some("bc")
            assert su.drop_first((2, "abc")) == sp.Some("c")
            assert su.drop_first((3, "abc")) == sp.Some("")
            assert su.drop_first((4, "abc")) == None
            assert su.drop_first((5, "abc")) == None

        @sp.private
        def test_split(self):
            assert sp.pack(su.split((" ", " "))) == sp.pack(
                sp.cast([], sp.list[sp.string])
            )
            assert sp.pack(su.split(("", " "))) == sp.pack(
                sp.cast([], sp.list[sp.string])
            )
            assert sp.pack(su.split(("abc def", "-"))) == sp.pack(["abc def"])
            assert sp.pack(su.split(("abc def", " "))) == sp.pack(["abc", "def"])
            assert sp.pack(su.split(("abc def ", " "))) == sp.pack(["abc", "def"])
            assert sp.pack(su.split(("      abc   def     ", " "))) == sp.pack(
                ["abc", "def"]
            )
            assert sp.pack(su.split(("abc def ghi", " "))) == sp.pack(
                ["abc", "def", "ghi"]
            )
            assert sp.pack(su.split(("abc def ghi ", " "))) == sp.pack(
                ["abc", "def", "ghi"]
            )
            assert sp.pack(su.split(("abc     def ghi ", " "))) == sp.pack(
                ["abc", "def", "ghi"]
            )
            assert sp.pack(su.split(("abc,def,ghi", ","))) == sp.pack(
                ["abc", "def", "ghi"]
            )
            assert sp.pack(su.split(("abc##def##ghi##", "##"))) == sp.pack(
                ["abc", "def", "ghi"]
            )

        @sp.private
        def test_starts_with(self):
            assert not su.starts_with(("abc", ""))
            assert not su.starts_with(("abc", "ab"))
            assert su.starts_with(("abc", "abc"))
            assert su.starts_with(("abc", "abcd"))
            assert su.starts_with(("abc", "abcdefg"))

        @sp.private
        def test_find_first(self):
            assert su.find_first((".", "abc")) == None
            assert su.find_first((".", ".abc")) == sp.Some(0)
            assert su.find_first((".", "a.bc")) == sp.Some(1)
            assert su.find_first((".", "ab.c")) == sp.Some(2)
            assert su.find_first((".", "abc.")) == sp.Some(3)
            assert su.find_first(("/", "4/6")) == sp.Some(1)

        @sp.private
        def test_from_digit(self):
            assert su.from_digit(0) == "0"
            assert su.from_digit(1) == "1"
            assert su.from_digit(2) == "2"
            assert su.from_digit(3) == "3"
            assert su.from_digit(4) == "4"
            assert su.from_digit(5) == "5"
            assert su.from_digit(6) == "6"
            assert su.from_digit(7) == "7"
            assert su.from_digit(8) == "8"
            assert su.from_digit(9) == "9"

        @sp.private
        def test_from_int(self):
            assert su.from_int(1) == "1"
            assert su.from_int(2) == "2"
            assert su.from_int(3) == "3"
            assert su.from_int(123) == "123"
            assert su.from_int(-123) == "-123"

        @sp.private
        def test_from_rational(self):
            assert su.from_rational(rational.mk((4, 3))) == "4/3"
            assert su.from_rational(rational.mk((-4, 3))) == "-4/3"
            assert su.from_rational(rational.mk((2, 6))) == "1/3"

        @sp.private
        def test_from_fixed_point(self):
            assert su.from_fixed_point(fp.mk((123, 2))) == "1.23"

        @sp.private
        def test_to_digit(self):
            assert su.to_digit("1") == 1
            assert su.to_digit("2") == 2
            assert su.to_digit("3") == 3
            assert su.to_digit("4") == 4
            assert su.to_digit("5") == 5
            assert su.to_digit("6") == 6
            assert su.to_digit("7") == 7
            assert su.to_digit("8") == 8
            assert su.to_digit("9") == 9

        @sp.private
        def test_to_int(self):
            assert su.to_int("1") == 1
            assert su.to_int("12") == 12
            assert su.to_int("123") == 123
            assert su.to_int("1234") == 1234

        @sp.private
        def test_to_rational(self):
            assert su.to_rational("4/6") == rational.mk((2, 3))
            assert su.to_rational("4/60") == rational.mk((2, 30))
            assert su.to_rational("04/60") == rational.mk((2, 30))
            assert su.to_rational("0/3") == rational.mk((0, 3))

        @sp.entrypoint
        def ep(self):
            self.test_drop_first()
            self.test_split()
            self.test_starts_with()
            self.test_find_first()
            self.test_from_digit()
            self.test_from_int()
            self.test_from_rational()
            self.test_from_fixed_point()
            self.test_to_digit()
            self.test_to_int()
            self.test_to_rational()


@sp.add_test()
def test():
    s = sp.test_scenario("Test")
    c = M.C()
    s += c
    c.ep()
