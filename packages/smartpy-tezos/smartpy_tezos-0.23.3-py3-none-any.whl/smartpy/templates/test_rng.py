import smartpy as sp

if "main" in __name__:

    @sp.add_test()
    def test():
        sc = sp.test_scenario("Test")
        main = sc.add_module("smartpy/templates/rng.spy")
        threefry = sc.add_module("smartpy/templates/threefry.spy")

        _x = threefry.max_rounds
        _tt = threefry.four_digit
        t = threefry.Threefry4x64(20)
        sc += t

        c1 = main.Rng(t.address)
        sc += c1
        if sc.simulation_mode() is sp.SimulationMode.MOCKUP:
            sc.p("mockups - TODO cant compile test ticket")
            return

        alice = sp.test_account("alice")
        seed = sp.record(i0=0, i1=0, i2=0, i3=0)
        ctr = sp.record(i0=0, i1=0, i2=0, i3=0)
        data = sp.record(seed=seed, ctr=ctr)
        c1.add_ticket((0, sp.test_ticket(alice.address, data, 1)))
        c1.send_ticket(key=0, receiver=alice.address)
