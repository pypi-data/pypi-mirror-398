import smartpy as sp


@sp.module
def M1():
    t: type = int
    u: type = sp.mutez


@sp.module
def M2():
    import M1

    t: type = bool
    u: type = tuple[M1.t, M1.u, t]
    v: type = sp.tuple[M1.t, M1.u, t]

    class C(sp.Contract):
        def __init__(self, y):
            self.data.x = y

        @sp.entrypoint
        def myEntryPoint(self, params):
            sp.cast(params, u)
            sp.cast(params, tuple[int, sp.mutez, bool])


@sp.module
def M3():
    import M2

    class C(sp.Contract):
        @sp.entrypoint
        def myEntryPoint(self, params):
            sp.cast(params, M2.u)
            sp.cast(params, sp.tuple[sp.int, sp.mutez, sp.bool])


@sp.add_test()
def test():
    s = sp.test_scenario("Abbrevs")

    s.add_module(M2)
    s.add_module(M3)

    c = M3.C()
    s += c
    if s.simulation_mode() is sp.SimulationMode.MOCKUP:
        s.p("mockups - TODO tuples>2")
    else:
        c.myEntryPoint(
            sp.set_type_expr(
                (1, sp.mutez(2), True), sp.tuple[sp.int, sp.mutez, sp.bool]
            )
        )
        c.myEntryPoint(sp.set_type_expr((1, sp.mutez(2), True), M2.u))

    c = M2.C(42)
    s += c
    if s.simulation_mode() is sp.SimulationMode.MOCKUP:
        s.p("mockups - TODO tuples>2")
    else:
        c.myEntryPoint(sp.set_type_expr((1, sp.mutez(2), True), M2.u))
