# Strings and Bytes - Example for illustrative purposes only.

import smartpy as sp


@sp.module
def main():
    # A few helper functions that have probably no place in a real world
    # smart contract but show general string manipulation techniques.

    def string_split(params):
        (s, sep) = params
        prev_idx = 0
        res = []
        for idx in range(sp.len(s)):
            if sp.slice(idx, 1, s).unwrap_some() == sep:
                res.push(sp.slice(prev_idx, sp.as_nat(idx - prev_idx), s).unwrap_some())
                prev_idx = idx + 1
        if sp.len(s) > 0:
            res.push(
                sp.slice(prev_idx, sp.as_nat(sp.len(s) - prev_idx), s).unwrap_some()
            )
        return reversed(res)

    def string_of_nat(params):
        c = {
            0: "0",
            1: "1",
            2: "2",
            3: "3",
            4: "4",
            5: "5",
            6: "6",
            7: "7",
            8: "8",
            9: "9",
        }
        x = params
        res = []
        if x == 0:
            res.push("0")
        while 0 < x:
            res.push(c[sp.mod(x, 10)])
            x /= 10
        return sp.concat(res)

    def nat_of_string(params):
        c = {
            "0": 0,
            "1": 1,
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
            "7": 7,
            "8": 8,
            "9": 9,
        }
        res = 0
        for idx in range(sp.len(params)):
            res = 10 * res + c[sp.slice(idx, 1, params).unwrap_some()]
        return res

    class MyContract(sp.Contract):
        def __init__(self):
            self.data.s0 = sp.Some("hello")
            self.data.b0 = sp.Some(sp.bytes("0xAA"))
            self.data.l0 = 0
            self.data.l1 = 0
            self.data.split = []
            self.data.string_of_nat = ""
            self.data.nat_of_string = 0

        @sp.entrypoint
        def concatenating(self, b0, b1, s, sb):
            # Concatenating a list of strings or a list of bytes
            self.data.s0 = sp.Some(sp.concat(s))
            self.data.b0 = sp.Some(sp.concat([b0, b1, sp.concat(sb)]))

        @sp.entrypoint
        def concatenating2(self, b1, b2, s1, s2):
            # Concatenating a two strings or two bytes
            self.data.s0 = sp.Some(s1 + s2)
            self.data.b0 = sp.Some(b1 + b2)

        @sp.entrypoint
        def slicing(self, b, s):
            # Slicing a string or a byte (this returns an option)
            self.data.s0 = sp.slice(2, 5, s)
            self.data.b0 = sp.slice(1, 2, b)

            # Computing length with sp.len
            self.data.l0 = sp.len(s)
            match self.data.s0:
                case Some(arg):
                    self.data.l0 += sp.len(arg)
            self.data.l1 = sp.len(b)

        @sp.entrypoint
        def test_split(self, params):
            self.data.split = string_split((params, ","))

        @sp.entrypoint
        def test_string_of_nat(self, params):
            self.data.string_of_nat = string_of_nat(params)

        @sp.entrypoint
        def test_nat_of_string(self, params):
            self.data.nat_of_string = nat_of_string(params)


# Tests
@sp.add_test()
def test():
    scenario = sp.test_scenario("String Manipulations")
    scenario.h1("String Manipulations")
    c1 = main.MyContract()
    scenario += c1

    c1.slicing(s="012345678901234567890123456789", b=sp.bytes("0xAA00BBCC"))
    scenario.verify_equal(c1.data.s0, sp.Some("23456"))
    scenario.verify_equal(c1.data.b0, sp.Some(sp.bytes("0x00BB")))
    scenario.verify_equal(c1.data.l0, 35)
    scenario.verify_equal(c1.data.l1, 4)
    c1.slicing(s="01", b=sp.bytes("0xCC"))
    scenario.verify_equal(c1.data.s0, None)
    # This one fails on sandbox because of missing type:
    scenario.verify_equal(c1.data.b0, None)

    c1.concatenating(
        s=["01", "234", "567", "89"],
        sb=[sp.bytes("0x1234"), sp.bytes("0x"), sp.bytes("0x4567aabbCCDD")],
        b0=sp.bytes("0x11"),
        b1=sp.bytes("0x223344"),
    )
    scenario.verify_equal(c1.data.s0, sp.Some("0123456789"))
    scenario.verify_equal(c1.data.b0, sp.Some(sp.bytes("0x1122334412344567AABBCCDD")))

    c1.concatenating2(s1="abc", s2="def", b1=sp.bytes("0xaaaa"), b2=sp.bytes("0xab"))

    c1.test_split("abc,def,ghi,,j")

    c1.test_string_of_nat(0)

    scenario.verify_equal(c1.data.string_of_nat, "0")

    c1.test_string_of_nat(12345678901234)

    c1.test_nat_of_string("12312345678901234123")

    scenario.show(c1.data)
    scenario.verify_equal(
        c1.data,
        sp.record(
            b0=sp.Some(sp.bytes("0xaaaaab")),
            l0=2,
            l1=1,
            s0=sp.Some("abcdef"),
            split=["abc", "def", "ghi", "", "j"],
            string_of_nat="12345678901234",
            nat_of_string=12312345678901234123,
        ),
    )
