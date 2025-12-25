import smartpy as sp


@sp.module
def main():
    def same_underlying_address(params):
        (a, b) = params
        sp.cast(a, sp.address)
        sp.cast(b, sp.address)
        b1 = sp.slice(6, 22, sp.pack(a))
        b2 = sp.slice(6, 22, sp.pack(b))
        return b1 == b2

    class TestAddressComparison(sp.Contract):
        def __init__(self, x, y):
            self.data.x = x
            self.data.y = y

        @sp.entrypoint
        def test(self, params):
            assert same_underlying_address(params)

        @sp.entrypoint
        def ep(self, a):
            assert self.isKT1(a), "Not KT1"
            self.data.x = a < sp.address("KT1XvNYseNDJJ6Kw27qhSEDF8ys8JhDopzfG")
            self.data.y = a >= sp.address("KT18amZmM5W7qDWVt2pH6uj7sCEd3kbzLrHT")

        @sp.private()
        def isKT1(self, address):
            return address <= sp.address(
                "KT1XvNYseNDJJ6Kw27qhSEDF8ys8JhDopzfG"
            ) and address >= sp.address("KT18amZmM5W7qDWVt2pH6uj7sCEd3kbzLrHT")


@sp.add_test()
def test():
    scenario = sp.test_scenario("TestAddressComparison")
    c1 = main.TestAddressComparison(x=False, y=False)

    scenario += c1

    alice = sp.test_account("alice")
    c1.ep(alice.address, _valid=False)
    c1.ep(sp.address("KT1TezoooozzSmartPyzzSTATiCzzzwwBFA1"))

    c1.test(
        (
            sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU"),
            sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU"),
        )
    )

    c1.test(
        (
            sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU"),
            sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU%a"),
        )
    )

    c1.test(
        (
            sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU"),
            sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU%"),
        )
    )

    c1.test(
        (
            sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU"),
            sp.address("tz1Z6Uk4qfdAJLJuCdGzL8aheqedW8sBQv2T"),
        ),
        _valid=False,
    )

    c1.test(
        (
            sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU"),
            sp.address("KT1AYAtnyeZKifkjv5ooKXsKuWWbpECMgoUC"),
        ),
        _valid=False,
    )

    c1.test(
        (
            sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU"),
            sp.address("KT1AYAtnyeZKifkjv5ooKXsKuWWbpECMgoUC%"),
        ),
        _valid=False,
    )
