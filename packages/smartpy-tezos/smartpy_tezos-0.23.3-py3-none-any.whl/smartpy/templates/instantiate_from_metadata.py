import smartpy as sp


@sp.module
def main():
    import smartpy.stdlib.math as m
    import smartpy.stdlib.utils as utils

    class MyContract(sp.Contract):
        """My Contract"""

        def __init__(self):
            self.data.x = "Test"
            self.data.y = 0

        @sp.entrypoint
        def ep(self, x):
            self.data.x = x
            self.data.y = m.pow((2, 3))

        @sp.offchain_view
        def add_10(self, n: sp.nat):
            """This adds 10."""
            return n + 10

    class MyContract2(sp.Contract):
        """My Contract"""

        def __init__(self):
            self.data.x = "Test"
            self.data.y = 0

        @sp.entrypoint
        def ep(self):
            self.data.y = utils.mutez_to_nat(sp.mutez(20))

        @sp.offchain_view
        def add_10(self, n: sp.nat):
            """This adds 10."""
            return n + 10


if "templates" not in __name__:

    @sp.add_test()
    def test():
        sc = sp.test_scenario("Test")
        c1 = main.MyContract()
        sc += c1
        c2 = main.MyContract2()
        sc += c2

        source = c1.get_source()
        metadata = sp.create_tzip16_metadata()
        current_version = f"SmartPy-{sp.config.version}"
        metadata["source"] = {"tools": [current_version]}
        # We check that sp.instantiate_from_metadata works.
        micheline = sp.instantiate_from_metadata(metadata, source)
        # The produced Michelson is equivalent to the one produced by the scenario.
        equivalent, _ = sp.are_equivalent_micheline(
            c1.get_generated_michelson(), micheline
        )
        assert equivalent

        # We check that it fails when providing an incorrect SmartPy version.
        metadata["source"]["tools"][0] = "SmartPy-0.0.0"
        try:
            sp.instantiate_from_metadata(metadata, source)
        except:
            pass
        else:
            assert (
                False
            ), "Instantiate from metadata only accepts metadata version == current version"

        metadata["source"]["tools"][0] = current_version

        # We check that the produced Michelson is different to the one produced by another contract from the scenario.
        equivalent, errors = sp.are_equivalent_micheline(
            c2.get_generated_michelson(), micheline
        )
        assert not equivalent and errors == [0, "args", 0, "args", 1, "prim"]
