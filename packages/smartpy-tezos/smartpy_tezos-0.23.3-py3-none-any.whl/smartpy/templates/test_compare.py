import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        @sp.entrypoint
        def compare_inferior(self):
            assert sp.compare(sp.nat(1), sp.nat(5)) == -1
            assert sp.compare(sp.int(1), sp.int(5)) == -1
            assert sp.compare(sp.timestamp(1), sp.timestamp(5)) == -1
            assert (
                sp.compare(
                    sp.address("KT18amZmM5W7qDWVt2pH6uj7sCEd3kbzLrHT"),
                    sp.address("KT1XvNYseNDJJ6Kw27qhSEDF8ys8JhDopzfG"),
                )
                == -1
            )
            assert sp.compare(False, True) == -1
            assert sp.compare(sp.bytes("0x00"), sp.bytes("0x01")) == -1
            assert sp.compare(sp.chain_id("0x00"), sp.chain_id("0x01")) == -1
            assert (
                sp.compare(
                    sp.key("edpkuBknW28nW72KG6RoH"), sp.key("edpkuJqtDcA2m2muMxViS")
                )
                == -1
            )
            assert (
                sp.compare(
                    sp.key_hash("tz1KqTpEZ7Yob7QbPE4Hy"),
                    sp.key_hash("tz1XPTDmvT3vVE5Uunngm"),
                )
                == -1
            )
            assert sp.compare(sp.mutez(1), sp.mutez(5)) == -1
            assert sp.compare("a", "e") == -1
            assert sp.compare((1, 5), (5, 1)) == -1
            assert sp.compare(None, sp.Some(())) == -1
            assert sp.compare(sp.Some(1), sp.Some(5)) == -1

            assert (
                sp.compare(sp.cast(sp.Left(5), sp.or_[sp.nat, sp.nat]), sp.Right(1))
                == -1
            )
            assert (
                sp.compare(sp.cast(sp.Left(1), sp.or_[sp.nat, sp.nat]), sp.Left(5))
                == -1
            )
            assert (
                sp.compare(sp.cast(sp.Left(1), sp.or_[sp.nat, sp.nat]), sp.Left(5))
                == -1
            )
            assert (
                sp.compare(sp.cast(sp.Right(1), sp.or_[sp.nat, sp.nat]), sp.Right(5))
                == -1
            )

        @sp.entrypoint
        def compare_eq(self):
            assert sp.compare((), ()) == 0
            assert (
                sp.compare(
                    sp.cast(None, sp.option[sp.nat]), sp.cast(None, sp.option[sp.nat])
                )
                == 0
            )
            assert sp.compare(sp.nat(2), sp.nat(1)) == 1


@sp.add_test()
def test():
    scenario = sp.test_scenario("Compare")
    if scenario.simulation_mode() is sp.SimulationMode.MOCKUP:
        scenario.p('mockup mode - cant originate with sp.chain_id("0x01")')
        return

    scenario.h1("Compare")
    c = main.C()
    scenario += c
    c.compare_inferior()
    c.compare_eq()
