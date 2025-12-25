# Data Layout - Example for illustrative purposes only.

import smartpy as sp


@sp.module
def main():
    class TestLayout(sp.Contract):
        def __init__(self):
            self.data.a = 1
            self.data.b = 12
            sp.cast(self.data, sp.record(a=sp.int, b=sp.nat).layout(("b", "a")))
            # self.init_entrypoints_layout(((("run_record", "run_record_2"), "run_type_record"), ("run_variant", "run_type_variant")))

        @sp.entrypoint
        def run_record(self, params):
            sp.cast(
                params,
                sp.record(a=sp.int, b=sp.string, c=sp.bool).layout(("b", ("a", "c"))),
            )

        # @sp.entrypoint
        # def run_record_2(self, params):
        #     sp.cast(params, sp.record(a = sp.int, b = sp.string, c = sp.bool, d = sp.nat).right_comb())

        @sp.entrypoint
        def run_variant(self, params):
            sp.cast(
                params,
                sp.variant(a=sp.int, b=sp.string, c=sp.bool).layout(("b", ("a", "c"))),
            )

        @sp.entrypoint
        def run_type_record(self, params):
            sp.cast(params, sp.record(a=sp.int, b=sp.string).layout(("b", "a")))

        @sp.entrypoint
        def run_type_variant(self, params):
            sp.cast(params, sp.variant(e=sp.int, d=sp.string).layout(("e", "d")))


@sp.add_test()
def test():
    scenario = sp.test_scenario("Layout")
    scenario.h1("Layout")
    scenario += main.TestLayout()
