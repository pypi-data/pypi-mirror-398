# Maps - Example for illustrative purposes only.

import smartpy as sp


@sp.module
def main():
    class Test_maps(sp.Contract):
        def __init__(self):
            self.data.x = "a"
            self.data.y = None
            self.data.z = sp.Some("na")
            self.data.m = {}

        @sp.entrypoint
        def test_map_get(self, params):
            sp.cast(params, map[sp.int, sp.string])
            self.data.x = params[12]

        @sp.entrypoint
        def test_map_get2(self, params):
            sp.cast(params, sp.map[int, sp.string])
            self.data.x = params[12]

        @sp.entrypoint
        def test_map_get_opt(self, params):
            sp.cast(params, map[int, sp.string])
            self.data.y = params.get_opt(12)

        @sp.entrypoint
        def test_map_get_default_values(self, params):
            sp.cast(params, map[int, sp.string])
            self.data.x = params.get(12, default="abc")

        @sp.entrypoint
        def test_map_get_missing_value(self, params):
            sp.cast(params, map[int, sp.string])
            self.data.x = params.get(12, error="missing 12")

        @sp.entrypoint
        def test_map_get_missing_value2(self, params):
            sp.cast(params, map[int, sp.string])
            self.data.x = params.get(12, error=1234)

        @sp.entrypoint
        def test_update_map(self):
            self.data.m = sp.update_map(1, sp.Some("one"), self.data.m)

        @sp.entrypoint
        def test_get_and_update(self):
            (previous_value, new_map) = sp.get_and_update(
                1, sp.Some("one"), self.data.m
            )
            self.data.z = previous_value


@sp.add_test()
def test():
    scenario = sp.test_scenario("Maps")
    c1 = main.Test_maps()
    scenario.h1("Maps")
    scenario += c1
    c1.test_map_get_opt({})
    c1.test_map_get_opt({12: "A"})
