import smartpy as sp

if "main" in __name__:

    @sp.add_test()
    def test():
        scenario = sp.test_scenario("Threefry4x64")
        rng = scenario.add_module("smartpy/templates/threefry.spy")

        c1 = rng.Threefry4x64(20)
        scenario.h1("Random123 on-chain")
        scenario += c1

        # test with some of the KAT test data for nrounds=20:
        # https://github.com/DEShawResearch/random123/blob/9545ff6413f258be2f04c1d319d99aaef7521150/tests/kat_vectors#L78
        seed = sp.record(i0=0, i1=0, i2=0, i3=0)
        ctr = sp.record(i0=0, i1=0, i2=0, i3=0)
        r = c1.rand(sp.record(seed=seed, ctr=ctr))
        scenario.show(r)
        scenario.verify(r.i0 == 657963966844654903)
        scenario.verify(r.i1 == 6166588228550287621)
        scenario.verify(r.i2 == 5463532747209585884)
        scenario.verify(r.i3 == 17161507908560806923)

        ff = 18446744073709551616 - 1  # 2 ^ 64 - 1
        seed = sp.record(i0=ff, i1=ff, i2=ff, i3=ff)
        ctr = sp.record(i0=ff, i1=ff, i2=ff, i3=ff)
        r = c1.rand(sp.record(seed=seed, ctr=ctr))
        scenario.show(r)
        scenario.verify(r.i0 == 3009038520807045659)
        scenario.verify(r.i1 == 248186141452226065)
        scenario.verify(r.i2 == 4333342425934739996)
        scenario.verify(r.i3 == 14783366217828847976)
