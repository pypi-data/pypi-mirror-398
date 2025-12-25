import smartpy as sp


@sp.module
def main():
    class C(sp.Contract):
        @sp.entrypoint
        def ep(self, params):
            sp.cast(
                params,
                sp.list[
                    sp.variant(
                        V1=sp.record(b=sp.string, a=sp.bool).layout(("b", "a")),
                        V2=sp.nat,
                    ).layout(("V2", "V1"))
                ],
            )


@sp.add_test()
def test():
    scenario = sp.test_scenario("C")
    scenario.h1("Toto")
    c = main.C()
    scenario += c
    c.ep([sp.variant("V1", sp.record(a=False, b="BBB"))])
