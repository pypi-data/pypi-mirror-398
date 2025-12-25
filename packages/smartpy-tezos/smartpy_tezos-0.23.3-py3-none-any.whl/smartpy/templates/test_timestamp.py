import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        def __init__(self):
            self.data.out = False
            self.data.next = sp.timestamp(0)
            self.data.before = sp.timestamp(-1)

        @sp.entrypoint
        def ep(self):
            self.data.out = sp.now > sp.add_seconds(sp.now, 1)
            assert sp.add_seconds(sp.now, 12) - sp.now == 12
            assert sp.now - sp.add_seconds(sp.now, 12) == -12
            assert sp.now - sp.add_seconds(sp.now, 12) == -12
            assert sp.add(sp.now, sp.int(500)) == sp.timestamp(1500)
            assert sp.add(sp.int(500), sp.now) == sp.timestamp(1500)
            self.data.next = sp.add_seconds(sp.now, 24 * 3600)
            assert sp.timestamp_from_utc(1, 1, 1, 0, 0, 0) == sp.timestamp(-62135596800)
            assert sp.timestamp_from_utc(1970, 1, 1, 0, 0, 0) == sp.timestamp(0)
            assert sp.timestamp_from_utc(2019, 9, 26, 10, 59, 51) == sp.timestamp(
                1569495591
            )


@sp.add_test()
def test():
    scenario = sp.test_scenario("Timestamp")
    scenario.h1("Timestamps")
    c = main.C()
    scenario += c
    if scenario.simulation_mode() is sp.SimulationMode.MOCKUP:
        scenario.p("mockups - TODO timestamps")
    else:
        c.ep(_now=sp.timestamp(1000))
